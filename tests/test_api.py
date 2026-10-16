import json
import threading
import urllib.error
import urllib.request
import pytest
from ecaps.api import make_server
from ecaps.backend import MockBackend
from ecaps.node import Node
from ecaps.power import PowerManager


@pytest.fixture
def served():
    node = Node(lambda plan: (MockBackend(lambda p: '{"tool":"noop","args":{}}'), lambda: None),
                PowerManager(4, 8), battery_pct=50)
    srv = make_server(node, port=0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield node, f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown(); srv.server_close()


def get(url):
    with urllib.request.urlopen(url, timeout=5) as r:
        return r.status, json.loads(r.read())


def test_status(served):
    node, base = served
    node.step()
    code, d = get(base + "/status")
    assert code == 200 and d["backend"]["is_mock"] is True and d["power"]["plan"]["mode"] == "normal"
    assert d["last_sensors"]["soil_moisture"] == 50.0 and "software setting" in d["memory_budget_note"]
    assert d["cloud_fallback"].startswith("off")


def test_models_marks_active_and_fit(served):
    _, base = served
    d = get(base + "/models")[1]
    by = {m["name"]: m for m in d["models"]}
    assert by["phi-3.5-mini-instruct"]["active"] and by["phi-3.5-mini-instruct"]["fits_budget"]
    assert not by["qwen2.5-7b-instruct"]["fits_budget"]
    assert all(m["gguf_present"] is False for m in d["models"])    # nothing downloaded here


def test_metrics_counts_steps_and_labels_proxy(served):
    node, base = served
    for _ in range(3): node.step()
    d = get(base + "/metrics")[1]
    assert d["steps"] == 3 and d["valid_actions"] == 3 and d["mean_latency_s"] is not None
    assert "PROXY" in d["note"]


def test_follows_power_change(served):
    node, base = served
    node.set_power(5)
    assert get(base + "/status")[1]["power"]["plan"]["mode"] == "eco"
    assert get(base + "/metrics")[1]["mode_switches"] == 1


def test_404_and_read_only(served):
    _, base = served
    with pytest.raises(urllib.error.HTTPError) as e: get(base + "/nope")
    assert e.value.code == 404
    req = urllib.request.Request(base + "/status", data=b"{}", method="POST")
    with pytest.raises(urllib.error.HTTPError) as e: urllib.request.urlopen(req, timeout=5)
    assert e.value.code == 405


def test_default_bind_is_loopback(served):
    node, _ = served
    srv = make_server(node, port=0)
    assert srv.server_address[0] == "127.0.0.1"
    srv.server_close()


def test_node_steps_from_background_thread(served):
    """Regression: the CLI steps the node in a worker thread; SQLite memory must allow that."""
    node, base = served
    errs = []
    def work():
        try:
            for _ in range(3): node.step()
        except Exception as e: errs.append(e)
    t = threading.Thread(target=work); t.start(); t.join()
    assert errs == [] and get(base + "/metrics")[1]["steps"] == 3
