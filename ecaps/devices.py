"""Device interface. Default = simulated sensor feed (no hardware needed).
Serial/ESP32 and MQTT adapters are stretch items and not implemented yet."""
from __future__ import annotations


class SimulatedSensors:
    def __init__(self, values: dict[str, float] | None = None):
        self.values = dict(values or {"soil_moisture": 50.0, "tank_level": 80.0, "temperature": 25.0})

    def names(self): return list(self.values)
    def read(self, name): return self.values[name]
    def set(self, **kw): self.values.update(kw)
    def snapshot(self): return dict(self.values)
