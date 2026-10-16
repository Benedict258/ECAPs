"""Tools the agent can call. Each has a validated argument spec."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


class ActionError(ValueError):
    pass


MAX_ALERT_CHARS = 60   # keeps a log_alert action inside the smallest (eco) output-token cap


@dataclass
class Tool:
    name: str
    doc: str
    args: dict            # arg name -> allowed values (list) or type (str/int)
    fn: Callable

    def validate(self, args: dict) -> dict:
        if not isinstance(args, dict):
            raise ActionError("args must be an object")
        if set(args) != set(self.args):
            raise ActionError(f"{self.name} expects args {sorted(self.args)}, got {sorted(args)}")
        for k, spec in self.args.items():
            v = args[k]
            if isinstance(spec, list) and v not in spec:
                raise ActionError(f"{self.name}.{k} must be one of {spec}, got {v!r}")
            if spec is str and not isinstance(v, str):
                raise ActionError(f"{self.name}.{k} must be a string")
            if spec is str and len(v) > MAX_ALERT_CHARS:
                raise ActionError(f"{self.name}.{k} longer than {MAX_ALERT_CHARS} characters")
        return args


class Toolbox:
    def __init__(self, sensors, state: dict | None = None):
        self.sensors = sensors
        self.state = state if state is not None else {"pump": "off", "alerts": []}
        self.tools = {t.name: t for t in [
            Tool("set_pump", "Turn the water pump on or off", {"state": ["on", "off"]}, self._set_pump),
            Tool("log_alert", "Record an alert message", {"msg": str}, self._log_alert),
            Tool("read_sensor", "Read a sensor by name", {"name": sorted(sensors.names())}, self._read),
            Tool("noop", "Do nothing; everything is fine", {}, lambda: "ok"),
        ]}

    def _device(self, method: str, *args):
        fn = getattr(self.sensors, method, None)
        if fn is not None:
            try:
                fn(*args)
            except Exception as e:                      # DeviceError etc.: do not claim success
                raise ActionError(f"device error in {method}: {e}") from e

    def _set_pump(self, state):
        self._device("set_pump", state)                 # actuate first; only record on success
        self.state["pump"] = state
        return f"pump {state}"

    def _log_alert(self, msg):
        self._device("alert", msg)
        self.state["alerts"].append(msg)
        return "alert logged"
    def _read(self, name): return self.sensors.read(name)

    def describe(self) -> str:
        return "\n".join(f"- {t.name}({', '.join(f'{k}: {v}' for k, v in t.args.items())}): {t.doc}"
                         for t in self.tools.values())

    def json_schema(self) -> dict:
        return {"type": "object", "required": ["tool", "args"], "properties": {
            "tool": {"enum": list(self.tools)}, "args": {"type": "object"}}}

    def execute(self, action: dict):
        if not isinstance(action, dict) or "tool" not in action:
            raise ActionError("action must be an object with 'tool'")
        tool = self.tools.get(action["tool"])
        if tool is None:
            raise ActionError(f"unknown tool {action['tool']!r}")
        args = tool.validate(action.get("args", {}))
        return tool.fn(**args)
