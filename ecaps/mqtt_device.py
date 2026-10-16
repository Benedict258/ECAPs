"""MQTT adapter for the device interface (optional dependency: paho-mqtt). The simulated feed stays the default.

Topics (prefix defaults to 'ecaps/device1'):
  device -> node   <prefix>/sensors/<name>   payload: a number            (one sensor)
                   <prefix>/sensors          payload: JSON {"name": number, ...}
                   <prefix>/ack/pump|alert   payload: 'OK' or 'ERR <reason>'
  node -> device   <prefix>/cmd/read         payload: '' (ask for fresh readings)
                   <prefix>/cmd/pump         payload: 'on' | 'off'
                   <prefix>/cmd/alert        payload: text (<= 60 chars)

Status: tested ONLY against an in-memory fake broker (tests/test_mqtt_device.py). The paho wrapper has not been run
against a real broker or device. No TLS or client certificates are configured: use it on a trusted local network only.
"""
from __future__ import annotations

import json
import math
import re
import threading
import time
from typing import Callable, Optional

from .devices import DeviceError

NAME_RE = re.compile(r"^[a-z0-9_]{1,32}$")
MAX_PAYLOAD = 1024


class PahoClient:
    """Thin wrapper over paho-mqtt (v1 or v2 API). Callback signature: cb(topic: str, payload: bytes)."""

    def __init__(self, host: str, port: int = 1883, username: Optional[str] = None, password: Optional[str] = None,
                 keepalive: int = 30):
        try:
            import paho.mqtt.client as mqtt
        except ImportError:
            raise DeviceError("paho-mqtt is not installed. Run: pip install paho-mqtt "
                              "(or use the default simulated feed)") from None
        try:
            self._c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        except AttributeError:                       # paho-mqtt 1.x
            self._c = mqtt.Client()
        if username:
            self._c.username_pw_set(username, password)
        self._subs: list[tuple[str, Callable]] = []
        self._c.on_message = lambda c, u, m: [cb(m.topic, bytes(m.payload)) for pat, cb in self._subs if mqtt.topic_matches_sub(pat, m.topic)]
        try:
            self._c.connect(host, port, keepalive)
        except OSError as e:
            raise DeviceError(f"cannot connect to MQTT broker {host}:{port}: {e}") from e
        self._c.loop_start()

    def subscribe(self, topic: str, cb: Callable[[str, bytes], None]):
        self._subs.append((topic, cb))
        self._c.subscribe(topic)

    def publish(self, topic: str, payload: str):
        self._c.publish(topic, payload)

    def close(self):
        self._c.loop_stop(); self._c.disconnect()


class MqttSensors:
    def __init__(self, prefix: str = "ecaps/device1", client=None, timeout: float = 2.0, max_age_s: float = 30.0,
                 require_ack: bool = True):
        if not prefix or any(ch in prefix for ch in "#+") or prefix.startswith("/") or prefix.endswith("/"):
            raise DeviceError("bad MQTT topic prefix (no wildcards, no leading/trailing slash)")
        self.prefix, self.timeout, self.max_age, self.require_ack = prefix, timeout, max_age_s, require_ack
        self.client = client
        self._cv = threading.Condition()
        self._values: dict[str, tuple[float, float]] = {}      # name -> (value, monotonic time)
        self._acks: dict[str, tuple[int, str]] = {}            # cmd -> (sequence, payload)
        self.dropped = 0
        self.pump_state = "unknown"
        client.subscribe(f"{prefix}/sensors/+", self._on_message)
        client.subscribe(f"{prefix}/sensors", self._on_message)
        client.subscribe(f"{prefix}/ack/+", self._on_message)
        self.snapshot()                                          # fail early if the device is silent

    # ---- incoming
    def _put(self, name: str, v) -> bool:
        try:
            f = float(v)
        except (TypeError, ValueError):
            return False
        if isinstance(v, bool) or not math.isfinite(f) or not NAME_RE.match(name):
            return False
        self._values[name] = (f, time.monotonic())
        return True

    def _on_message(self, topic: str, payload: bytes):
        ok = False
        if len(payload) <= MAX_PAYLOAD and topic.startswith(self.prefix + "/"):
            rest = topic[len(self.prefix) + 1:]
            try:
                text = payload.decode("utf-8")
                with self._cv:
                    if rest == "sensors":
                        data = json.loads(text)
                        ok = isinstance(data, dict) and bool(data) and all([self._put(k, v) for k, v in data.items()])
                    elif rest.startswith("sensors/"):
                        ok = self._put(rest.split("/", 1)[1], text.strip())
                    elif rest.startswith("ack/"):
                        cmd = rest.split("/", 1)[1]
                        if cmd in ("pump", "alert"):
                            self._acks[cmd] = (self._acks.get(cmd, (0, ""))[0] + 1, text.strip())
                            ok = True
                    if ok:
                        self._cv.notify_all()
            except (UnicodeDecodeError, ValueError):
                ok = False
        if not ok:
            self.dropped += 1          # malformed / oversized / unknown: ignored, counted

    # ---- sensor interface
    def _fresh(self) -> Optional[dict[str, float]]:
        now = time.monotonic()
        if self._values and all(now - t <= self.max_age for _, t in self._values.values()):
            return {k: v for k, (v, _) in self._values.items()}
        return None

    def snapshot(self) -> dict[str, float]:
        with self._cv:
            snap = self._fresh()
            if snap:
                return snap
            before = {k: t for k, (_, t) in self._values.items()}
        self.client.publish(f"{self.prefix}/cmd/read", "")
        end = time.monotonic() + self.timeout
        with self._cv:
            while time.monotonic() < end:
                snap = self._fresh()
                if snap and any(self._values[k][1] != before.get(k) for k in snap):
                    return snap
                self._cv.wait(0.05)
        raise DeviceError("timeout: no fresh sensor readings from the MQTT device")

    def names(self): return list(self._values)

    def read(self, name):
        snap = self.snapshot()
        if name not in snap:
            raise DeviceError(f"device did not report sensor {name!r}")
        return snap[name]

    # ---- actuation
    def _command(self, cmd: str, payload: str):
        if "\n" in payload or "\r" in payload:
            raise DeviceError("newline in command argument")
        with self._cv:
            seq = self._acks.get(cmd, (0, ""))[0]
        self.client.publish(f"{self.prefix}/cmd/{cmd}", payload)
        if not self.require_ack:
            return "published (unacknowledged)"
        end = time.monotonic() + self.timeout
        with self._cv:
            while time.monotonic() < end:
                got = self._acks.get(cmd, (0, ""))
                if got[0] > seq:
                    if not got[1].startswith("OK"):
                        raise DeviceError(f"device rejected {cmd} {payload!r}: {got[1]}")
                    return got[1]
                self._cv.wait(0.05)
        raise DeviceError(f"timeout waiting for {cmd} acknowledgement")

    def set_pump(self, state: str):
        self._command("pump", state); self.pump_state = state

    def alert(self, msg: str): self._command("alert", msg)
    def close(self): self.client.close()
