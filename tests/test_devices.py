import json
import pytest
from ecaps.agent import Agent
from ecaps.backend import MockBackend
from ecaps.devices import (DeviceError, SerialSensors, SimulatedSensors, make_sensors,
                           parse_reading, format_command)
from ecaps.memory import Memory
from ecaps.tools import Toolbox


class FakeESP32Port:
    """In-memory stand-in for a pyserial port speaking the docs/ESP32.md protocol. NOT real hardware."""
    def __init__(self, readings=None, noise=True, silent=False, reject_pump=False):
        self.readings = readings or {"soil_moisture": 20.0, "tank_level": 75.0, "temperature": 24.5}
        self.out, self.noise, self.silent, self.reject_pump = [], noise, silent, reject_pump
        self.received, self.closed = [], False

    def write(self, b):
        line = b.decode().strip(); self.received.append(line)
        if self.silent: return
        if self.noise: self.out.append(b"boot: ets Jun 8 2016\n")
        if line == "R":
            self.out.append(("S " + " ".join(f"{k}={v}" for k, v in self.readings.items()) + "\n").encode())
        elif line.startswith("P "):
            self.out.append(b"ERR bad pump\n" if self.reject_pump else f"OK pump {line[2:]}\n".encode())
        elif line.startswith("A "):
            self.out.append(b"OK alert\n")

    def readline(self): return self.out.pop(0) if self.out else b""
    def close(self): self.closed = True


def serial(fake, **kw): return SerialSensors("FAKE", port_factory=lambda: fake, timeout=0.2, **kw)


def test_default_device_is_simulated():
    s = make_sensors({})
    assert isinstance(s, SimulatedSensors) and set(s.names()) == {"soil_moisture", "tank_level", "temperature"}


def test_simulated_script_advances_and_pump_recorded():
    s = SimulatedSensors(script=[{"soil_moisture": 10.0}, {"soil_moisture": 60.0}])
    assert s.advance()["soil_moisture"] == 10.0 and s.advance()["soil_moisture"] == 60.0
    assert s.advance()["soil_moisture"] == 60.0            # exhausted: stays
    s.set_pump("on"); assert s.pump_state == "on"


@pytest.mark.parametrize("bad", ["", "X a=1", "S", "S a", "S a=abc", "S a=nan", "S a=inf", "S Bad-Name=1", "S =3"])
def test_parse_rejects_malformed(bad):
    with pytest.raises(DeviceError): parse_reading(bad)


def test_parse_ok():
    assert parse_reading("S soil_moisture=41.5 temperature=-3") == {"soil_moisture": 41.5, "temperature": -3.0}


def test_command_rejects_newline_injection():
    with pytest.raises(DeviceError): format_command("A", "x\nP on")
    assert format_command("P", "on") == b"P on\n"


def test_serial_reads_and_ignores_noise():
    s = serial(FakeESP32Port())
    assert s.read("soil_moisture") == 20.0 and set(s.names()) == {"soil_moisture", "tank_level", "temperature"}


def test_serial_timeout_raises():
    with pytest.raises(DeviceError, match="timeout"):
        serial(FakeESP32Port(silent=True))


def test_serial_unknown_sensor():
    with pytest.raises(DeviceError): serial(FakeESP32Port()).read("nope")


def test_missing_pyserial_message(monkeypatch):
    import builtins
    real = builtins.__import__
    monkeypatch.setattr(builtins, "__import__", lambda n, *a, **k: (_ for _ in ()).throw(ImportError()) if n == "serial" else real(n, *a, **k))
    with pytest.raises(DeviceError, match="pyserial"): SerialSensors("COM9")


def test_agent_actuates_device_end_to_end():
    port = FakeESP32Port()
    s = serial(port)
    agent = Agent(MockBackend(lambda p: '{"tool":"set_pump","args":{"state":"on"}}'), Toolbox(s), Memory(":memory:"), s)
    r = agent.step()
    assert r.valid and "P on" in port.received and s.pump_state == "on" and agent.tools.state["pump"] == "on"


def test_device_rejection_is_reported_not_faked():
    port = FakeESP32Port(reject_pump=True)
    s = serial(port)
    agent = Agent(MockBackend(lambda p: '{"tool":"set_pump","args":{"state":"on"}}'), Toolbox(s), Memory(":memory:"), s)
    r = agent.step()
    assert not r.valid and "device error" in r.error and agent.tools.state["pump"] == "off"
