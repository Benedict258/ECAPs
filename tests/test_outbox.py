import http.server
import json
import socket
import threading
import pytest
from ecaps.backend import MockBackend
from ecaps.node import Node
from ecaps.outbox import ConfigError, HttpCloudSink, OutboxQueue, Syncer, make_sink
from ecaps.power import PowerManager


class FakeSink:
    def __init__(self, fail=True): self.fail, self.received = fail, []
    def send(self, records):
        if self.fail: raise ConnectionError("unreachable")
        self.received += records


def make_node(tmp=None, syncer=None, outbox=None, responder=None):
    return Node(lambda p: (MockBackend(responder or (lambda x: '{"tool":"noop","args":{}}')), lambda: None),
                PowerManager(4, 8), outbox=outbox, syncer=syncer)


@pytest.fixture
def no_network(monkeypatch):
    """Fail on ANY socket connect, loopback included."""
    attempts = []
    def guard(self, addr):
        attempts.append(addr); raise AssertionError(f"connection attempted: {addr}")
    monkeypatch.setattr(socket.socket, "connect", guard)
    return attempts


def test_queue_persists_and_keeps_order(tmp_path):
    p = str(tmp_path / "o.sqlite")
    q = OutboxQueue(p)
    ids = [q.enqueue("event", {"n": i}) for i in range(3)]
    q.close()
    q2 = OutboxQueue(p)
    assert [r["id"] for r in q2.pending()] == ids and [r["payload"]["n"] for r in q2.pending()] == [0, 1, 2]


def test_no_sink_means_no_network_and_items_stay_queued(no_network):
    q = OutboxQueue(":memory:")
    q.enqueue("event", {"a": 1})
    r = Syncer(q, None).sync_once()
    assert r["skipped"] and r["sent"] == 0 and r["pending"] == 1 and no_network == []


def test_cloud_disabled_by_default_in_config():
    assert make_sink({}) is None
    assert make_sink({"cloud": {"enabled": False, "url": "http://example.invalid"}}) is None
    with pytest.raises(ConfigError): make_sink({"cloud": {"enabled": True}})
    with pytest.raises(ConfigError): make_sink({"cloud": {"enabled": True, "url": "file:///etc/passwd"}})


def test_failed_sync_keeps_records_then_recovers_in_order():
    q = OutboxQueue(":memory:")
    for i in range(5): q.enqueue("action", {"i": i})
    sink = FakeSink(fail=True)
    s = Syncer(q, sink, batch_size=2)
    r = s.sync_once()
    assert "error" in r and r["pending"] == 5 and r["sent"] == 0
    assert all(x["attempts"] == 1 for x in q.pending(2)[:2])
    sink.fail = False
    r = s.sync_once()
    assert r["sent"] == 5 and r["pending"] == 0 and "error" not in r
    assert [x["payload"]["i"] for x in sink.received] == [0, 1, 2, 3, 4]
    assert len({x["id"] for x in sink.received}) == 5          # unique ids allow de-duplication downstream


def test_local_loop_works_with_all_network_blocked_and_queues_everything(no_network):
    q = OutboxQueue(":memory:")
    node = make_node(syncer=Syncer(q, None), outbox=q,
                     responder=lambda p: '{"tool":"log_alert","args":{"msg":"tank low"}}')
    for _ in range(3): node.step()
    assert node.metrics["valid_actions"] == 3
    c = q.counts()
    assert c["pending"] == 6 and c["sent"] == 0                 # 3 actions + 3 alert events
    assert node.sync()["skipped"] and no_network == []


def test_node_without_outbox_queues_nothing():
    node = make_node()
    node.step()
    assert node.outbox is None and node.sync()["skipped"]


def test_invalid_action_is_queued_as_event():
    q = OutboxQueue(":memory:")
    node = make_node(outbox=q, responder=lambda p: "garbage")
    node.step()
    kinds = [r["kind"] + ":" + str(r["payload"].get("type")) for r in q.pending()]
    assert kinds == ["action:None", "event:invalid_action"]


class _Handler(http.server.BaseHTTPRequestHandler):
    got = []
    def do_POST(self):
        body = self.rfile.read(int(self.headers["Content-Length"]))
        _Handler.got.append((json.loads(body), self.headers.get("Authorization")))
        self.send_response(200); self.end_headers()
    def log_message(self, *a): pass


def test_http_sink_against_localhost_server():
    _Handler.got = []
    srv = http.server.HTTPServer(("127.0.0.1", 0), _Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        q = OutboxQueue(":memory:")
        node = make_node(outbox=q)
        node.step()
        sink = HttpCloudSink(f"http://127.0.0.1:{srv.server_address[1]}/ingest", token="t0k")
        r = Syncer(q, sink).sync_once()
        assert r["sent"] == 1 and r["pending"] == 0
        assert _Handler.got[0][0]["records"][0]["kind"] == "action" and _Handler.got[0][1] == "Bearer t0k"
    finally:
        srv.shutdown(); srv.server_close()


def test_http_sink_unreachable_keeps_queue():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()   # a port nobody listens on
    q = OutboxQueue(":memory:")
    q.enqueue("event", {"x": 1})
    r = Syncer(q, HttpCloudSink(f"http://127.0.0.1:{port}/", timeout=1)).sync_once()
    assert "error" in r and r["pending"] == 1


def test_status_reports_outbox_state():
    from ecaps.api import status
    q = OutboxQueue(":memory:")
    node = make_node(outbox=q, syncer=Syncer(q, None))
    node.step()
    st = status(node)["outbox"]
    assert st == {"pending": 1, "sent": 0, "queueing": True, "cloud_sync_configured": False}
