import json
from ecaps import environment
from ecaps.backend import MockBackend


def test_environment_capture_and_save(tmp_path):
    p = tmp_path / "environment.json"
    env = environment.save(p)
    assert json.loads(p.read_text()) == env
    for k in ("cpu_model", "logical_threads", "ram_total_gb", "os", "runtime_commit", "date"):
        assert k in env
    assert env["ram_total_gb"] > 0


def test_footer_mentions_hardware():
    env = environment.capture()
    assert env["cpu_model"] in environment.footer_line(env)


def test_smoke_mock_generates_text():
    r = MockBackend().generate("hello", max_tokens=5)
    assert r.is_mock and r.text and r.n_tokens == 5
