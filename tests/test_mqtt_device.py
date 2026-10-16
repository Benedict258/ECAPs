"""MQTT adapter tests use an in-memory fake broker and a fake device. No real broker or hardware is involved."""
import socket
import threading
import pytest
from ecaps.agent import Agent
from ecaps.backend import MockBackend
from ecaps.devices import DeviceError, SimulatedSensors, make_sensors
from ecaps.memory import Memory
from ecaps.mqtt_device import MqttSensors
from ecaps.tools import Toolbox


def matches(pattern, topic):
    p, t = pattern.split("/"), topic.split("/")
    if len(p) != len(t): return False
    return all(a == "+" or a == b for a, b in zip(p, t))


class FakeBroker:
    def __init__(self): self.subs, self.log, self._lock = [], [], threading.Lock()
    def client(self): return FakeClient(self)
    def deliver(self, topic, payload):
        self.log.append((topic, payload))
        for pat, cb in list(self.subs):
            if matches(pat, topic): cb(topic, payload if isinstance(payload, bytes) else payload.encode())


class FakeClient:
    def __init__(self, broker): self.b, self.closed = broker, False
    def subscribe(self, topic, cb): self.b.subs.append((topic, cb))
    def publish(self, topic, payload): self.b.deliver(topic, payload)
    def close(self): self.closed = True


class FakeDevice:
    """Answers read/pump/alert commands like docs would describe. NOT real hardware."""
    def __init__(self, broker, prefix="ecaps/device1", readings=None, ack=True, reject_pump=False, silent=False):
        self.b, self.prefix, self.ack, self.reject_pump, self.silent = broker, prefix, ack, reject_pump, silent
        self.readings = readings or {"soil_moisture": 20.0, "tank_level": 75.0, "temperature": 24.5}
        self.pump = "off"
        broker.subs.append((f"{prefix}/cmd/+", self.on_cmd))

    def publish_readings(self):
        for k, v in self.readings.items(): self.b.deliver(f"{self.prefix}/sensors/{k}", str(v))

    def on_cmd(self, topic, payload):
        if self.silent: return
        cmd, text = topic.rsplit("/", 1)[1], payload.decode()
        if cmd == "read": self.publish_readings()
        elif cmd == "pump":
            if self.reject_pump: self.b.deliver(f"{self.prefix}/ack/pump", "ERR bad pump")
            else:
                self.pump = text
                if self.ack: self.b.deliver(f"{self.prefix}/ack/pump", "OK")
        elif cmd == "alert" and self.ack: self.b.deliver(f"{self.prefix}/ack/alert", "OK")


def sensors(broker=None, **dev_kw):
    broker = broker or FakeBroker()
    dev = FakeDevice(broker, **dev_kw)
    return MqttSensors("ecaps/device1", broker.client(), timeout=0.3, max_age_s=30), dev, broker


def test_default_remains_simulated():
    assert isinstance(make_sensors({}), SimulatedSensors)


def test_reads_via_request_and_caches():
    s, dev, b = sensors()
    assert s.read("soil_moisture") == 20.0 and set(s.names()) == {"soil_moisture", "tank_level", "temperature"}
    n = sum(1 for t, _ in b.log if t.endswith("cmd/read"))
    s.snapshot()                                   # fresh cache: no new request
    assert sum(1 for t, _ in b.log if t.endswith("cmd/read")) == n


def test_json_sensor_topic_supported():
    b = FakeBroker()
    b.subs.append(("ecaps/device1/cmd/+", lambda topic, payload: topic.endswith("cmd/read") and
                   b.deliver("ecaps/device1/sensors", '{"soil_moisture": 33, "temperature": 21.5}')))
    s = MqttSensors("ecaps/device1", b.client(), timeout=0.3)
    assert s.snapshot() == {"soil_moisture": 33.0, "temperature": 21.5}


def test_silent_device_times_out_at_construction():
    with pytest.raises(DeviceError, match="timeout"):
        sensors(silent=True)


def test_stale_readings_trigger_new_request_and_fail_if_unanswered():
    s, dev, b = sensors()
    s.max_age = 0.0                                 # everything is instantly stale
    dev.silent = True
    with pytest.raises(DeviceError, match="timeout"): s.snapshot()


@pytest.mark.parametrize("topic,payload", [("ecaps/device1/sensors/temp", "abc"), ("ecaps/device1/sensors/temp", "nan"),
                                           ("ecaps/device1/sensors/Bad-Name", "1"), ("ecaps/device1/sensors", "[1,2]"),
                                           ("ecaps/device1/sensors", '{"a": "x"}'), ("ecaps/device1/sensors/t", "1" * 2000),
                                           ("ecaps/device1/ack/other", "OK"), ("ecaps/device1/sensors/t", b"\xff\xfe")])
def test_malformed_messages_are_dropped(topic, payload):
    s, dev, b = sensors()
    before, names = s.dropped, set(s.names())
    b.deliver(topic, payload)
    assert s.dropped == before + 1 and set(s.names()) == names


def test_pump_acknowledged():
    s, dev, b = sensors()
    s.set_pump("on")
    assert dev.pump == "on" and s.pump_state == "on"


def test_pump_rejected_and_missing_ack_are_errors_not_success():
    s, dev, b = sensors(reject_pump=True)
    with pytest.raises(DeviceError, match="rejected"): s.set_pump("on")
    assert s.pump_state == "unknown"
    s2, dev2, _ = sensors(ack=False)
    with pytest.raises(DeviceError, match="timeout"): s2.set_pump("on")


def test_require_ack_false_reports_unacknowledged():
    b = FakeBroker(); dev = FakeDevice(b, ack=False)
    s = MqttSensors("ecaps/device1", b.client(), timeout=0.3, require_ack=False)
    assert s._command("pump", "on") == "published (unacknowledged)"


def test_bad_prefix_and_newline_rejected():
    for bad in ("", "a/#", "a/+/b", "/a", "a/"):
        with pytest.raises(DeviceError): MqttSensors(bad, FakeBroker().client())
    s, *_ = sensors()
    with pytest.raises(DeviceError): s.alert("x\nA y")


def test_agent_actuates_through_mqtt_end_to_end():
    s, dev, b = sensors()
    agent = Agent(MockBackend(lambda p: '{"tool":"set_pump","args":{"state":"on"}}'), Toolbox(s), Memory(":memory:"), s)
    r = agent.step()
    assert r.valid and dev.pump == "on" and agent.tools.state["pump"] == "on"


def test_device_rejection_reported_through_agent():
    s, dev, b = sensors(reject_pump=True)
    agent = Agent(MockBackend(lambda p: '{"tool":"set_pump","args":{"state":"on"}}'), Toolbox(s), Memory(":memory:"), s)
    r = agent.step()
    assert not r.valid and "device error" in r.error and agent.tools.state["pump"] == "off"


def test_make_sensors_mqtt_with_injected_client():
    b = FakeBroker(); FakeDevice(b)
    s = make_sensors({"device": {"type": "mqtt", "prefix": "ecaps/device1", "timeout": 0.3}}, mqtt_client=b.client())
    assert isinstance(s, MqttSensors) and s.read("tank_level") == 75.0


def test_paho_wrapper_reports_unreachable_broker_cleanly():
    pytest.importorskip("paho.mqtt.client")
    from ecaps.mqtt_device import PahoClient
    sk = socket.socket(); sk.bind(("127.0.0.1", 0)); port = sk.getsockname()[1]; sk.close()   # nothing listens here
    with pytest.raises(DeviceError, match="cannot connect"): PahoClient("127.0.0.1", port)


def test_missing_paho_message(monkeypatch):
    import builtins
    real = builtins.__import__
    def fake(n, *a, **k):
        if n.startswith("paho"): raise ImportError()
        return real(n, *a, **k)
    monkeypatch.setattr(builtins, "__import__", fake)
    from ecaps.mqtt_device import PahoClient
    with pytest.raises(DeviceError, match="paho-mqtt is not installed"): PahoClient("127.0.0.1")
