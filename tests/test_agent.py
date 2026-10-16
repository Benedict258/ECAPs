import json
import socket
import pytest
from ecaps.agent import Agent
from ecaps.backend import MockBackend
from ecaps.devices import SimulatedSensors
from ecaps.memory import Memory
from ecaps.tools import ActionError, Toolbox


def make(responder, tmp_path, **kw):
    s = SimulatedSensors()
    return Agent(MockBackend(responder), Toolbox(s), Memory(str(tmp_path / "m.sqlite")), s, **kw), s


def test_valid_action_executes(tmp_path):
    a, s = make(lambda p: json.dumps({"tool": "set_pump", "args": {"state": "on"}}), tmp_path)
    r = a.step()
    assert r.valid and a.tools.state["pump"] == "on"


@pytest.mark.parametrize("bad", ['not json', '{"tool":"launch_missile","args":{}}',
                                 '{"tool":"set_pump","args":{"state":"maybe"}}'])
def test_invalid_actions_rejected_not_executed(tmp_path, bad):
    a, _ = make(lambda p: bad, tmp_path)
    r = a.step()
    assert not r.valid and a.tools.state["pump"] == "off"


def test_memory_persists_across_instances(tmp_path):
    a, _ = make(lambda p: '{"tool":"noop","args":{}}', tmp_path)
    a.step(); a.memory.close()
    assert len(Memory(str(tmp_path / "m.sqlite")).recent()) == 1


def test_cloud_off_by_default_and_never_called(tmp_path):
    called = []
    a, _ = make(lambda p: "garbage", tmp_path, cloud_fallback=lambda p: called.append(1) or "{}")
    a.step()
    assert not called


def test_no_outbound_network_during_loop(tmp_path, monkeypatch):
    attempts = []
    real = socket.socket.connect

    def guard(self, addr):
        attempts.append(addr)
        raise AssertionError(f"outbound connection attempted: {addr}")
    monkeypatch.setattr(socket.socket, "connect", guard)
    a, _ = make(lambda p: '{"tool":"noop","args":{}}', tmp_path)
    for _ in range(3):
        a.step()
    assert attempts == []
