"""Device interface. The DEFAULT is a simulated sensor feed that needs no hardware.
A serial adapter (ESP32 or similar) speaks a small line protocol, see docs/ESP32.md.
The serial adapter has only been tested against an in-memory fake port, not a real ESP32."""
from __future__ import annotations

import math
import time
from typing import Callable, Optional

KNOWN_SENSOR_CHARS = set("abcdefghijklmnopqrstuvwxyz0123456789_")


class DeviceError(RuntimeError):
    pass


# ---------------------------------------------------------------- protocol helpers
def parse_reading(line: str) -> dict[str, float]:
    """Parse 'S name=value name=value ...'. Raises DeviceError on anything malformed."""
    parts = line.strip().split()
    if not parts or parts[0] != "S" or len(parts) < 2:
        raise DeviceError(f"not a reading line: {line!r}")
    out: dict[str, float] = {}
    for tok in parts[1:]:
        name, sep, val = tok.partition("=")
        if not sep or not name or set(name) - KNOWN_SENSOR_CHARS:
            raise DeviceError(f"bad sensor token {tok!r}")
        try:
            v = float(val)
        except ValueError:
            raise DeviceError(f"bad value in {tok!r}") from None
        if not math.isfinite(v):
            raise DeviceError(f"non-finite value in {tok!r}")
        out[name] = v
    return out


def format_command(kind: str, arg: str = "") -> bytes:
    if "\n" in arg or "\r" in arg:
        raise DeviceError("newline in command argument")
    return f"{kind} {arg}".rstrip().encode("ascii", "replace") + b"\n"


# ---------------------------------------------------------------- simulated feed (default)
class SimulatedSensors:
    def __init__(self, values: dict[str, float] | None = None, script: list[dict] | None = None):
        self.values = dict(values or {"soil_moisture": 50.0, "tank_level": 80.0, "temperature": 25.0})
        self.script, self._i = list(script or []), 0
        self.pump_state, self.alerts_sent = "off", []

    def names(self): return list(self.values)
    def read(self, name): return self.values[name]
    def set(self, **kw): self.values.update(kw)
    def snapshot(self): return dict(self.values)

    def advance(self):
        """Move to the next scripted snapshot (no-op when there is no script or it is exhausted)."""
        if self._i < len(self.script):
            self.values.update(self.script[self._i]); self._i += 1
        return self.snapshot()

    def set_pump(self, state: str): self.pump_state = state
    def alert(self, msg: str): self.alerts_sent.append(msg)


# ---------------------------------------------------------------- serial adapter
class SerialSensors:
    """Line protocol over a serial port. `port_factory` lets tests inject a fake port."""

    def __init__(self, port: str, baud: int = 115200, timeout: float = 2.0,
                 port_factory: Optional[Callable[[], object]] = None):
        if port_factory is None:
            try:
                import serial  # pyserial: optional dependency
            except ImportError:
                raise DeviceError("pyserial is not installed. Run: pip install pyserial "
                                  "(or use the default simulated feed)") from None
            port_factory = lambda: serial.Serial(port, baud, timeout=timeout)
        self.timeout = timeout
        self.port = port_factory()
        self._last: dict[str, float] = {}
        self.pump_state = "unknown"
        self.refresh()                      # fail early if the device is not answering

    def _readline(self) -> str:
        return self.port.readline().decode("ascii", "replace").strip()

    def _expect(self, prefixes: tuple[str, ...]) -> str:
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            line = self._readline()
            if not line:
                continue
            if line.startswith(prefixes):
                return line
            # anything else (boot logs, noise, unsolicited lines) is ignored
        raise DeviceError(f"timeout waiting for {prefixes} from device")

    def refresh(self) -> dict[str, float]:
        self.port.write(format_command("R"))
        self._last = parse_reading(self._expect(("S ",)))
        return dict(self._last)

    def names(self): return list(self._last)
    def snapshot(self): return self.refresh()

    def read(self, name):
        snap = self.refresh()
        if name not in snap:
            raise DeviceError(f"device did not report sensor {name!r}")
        return snap[name]

    def _command(self, kind: str, arg: str) -> str:
        self.port.write(format_command(kind, arg))
        line = self._expect(("OK", "ERR"))
        if line.startswith("ERR"):
            raise DeviceError(f"device rejected {kind} {arg!r}: {line}")
        return line

    def set_pump(self, state: str):
        self._command("P", state); self.pump_state = state

    def alert(self, msg: str): self._command("A", msg)
    def close(self): self.port.close()


def make_sensors(cfg: dict | None = None, mqtt_client=None):
    """cfg['device'] = {'type': 'simulated'} (default), {'type': 'serial', 'port': 'COM3'} or
    {'type': 'mqtt', 'host': '127.0.0.1', 'prefix': 'ecaps/device1'} (password from $ECAPS_MQTT_PASSWORD)."""
    d = (cfg or {}).get("device") or {"type": "simulated"}
    if d.get("type", "simulated") == "simulated":
        return SimulatedSensors(d.get("values"), d.get("script"))
    if d["type"] == "serial":
        return SerialSensors(d["port"], d.get("baud", 115200), d.get("timeout", 2.0))
    if d["type"] == "mqtt":
        import os
        from .mqtt_device import MqttSensors, PahoClient
        client = mqtt_client or PahoClient(d.get("host", "127.0.0.1"), d.get("port", 1883), d.get("username"),
                                           os.environ.get("ECAPS_MQTT_PASSWORD"))
        return MqttSensors(d.get("prefix", "ecaps/device1"), client, d.get("timeout", 2.0), d.get("max_age_s", 30.0),
                           d.get("require_ack", True))
    raise DeviceError(f"unknown device type {d['type']!r}")


if __name__ == "__main__":
    import argparse, json
    ap = argparse.ArgumentParser(description="Read one snapshot from a serial device (or the simulated feed).")
    ap.add_argument("--port"); ap.add_argument("--baud", type=int, default=115200)
    a = ap.parse_args()
    s = SerialSensors(a.port, a.baud) if a.port else SimulatedSensors()
    print(json.dumps(s.snapshot()))
