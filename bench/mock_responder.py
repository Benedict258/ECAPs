"""Rule-based stand-in for a model, used ONLY by --mock. Deliberately wrong on some tasks so failure
reporting is exercised. Output is DUMMY and says nothing about any real model."""
import json
import re


def responder(prompt: str) -> str:
    m = re.search(r"Sensors: (\{.*?\})", prompt)
    if not m:
        return json.dumps({"tool": "noop", "args": {}})
    s = json.loads(m.group(1))
    wrong = int(s["soil_moisture"] + s["tank_level"] + s["temperature"]) % 9 == 4   # deterministic "mistakes"
    if wrong:
        return json.dumps({"tool": "noop", "args": {}})
    if s["soil_moisture"] < 30:
        return json.dumps({"tool": "set_pump", "args": {"state": "on"}})
    if s["tank_level"] < 10:
        return json.dumps({"tool": "log_alert", "args": {"msg": "tank low"}})
    if s["temperature"] > 40:
        return json.dumps({"tool": "log_alert", "args": {"msg": "too hot"}})
    return json.dumps({"tool": "noop", "args": {}})
