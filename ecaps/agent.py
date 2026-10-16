"""Agent runtime: sense -> plan -> act. Local-first; cloud fallback is a stub, OFF by default."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Callable, Optional

from .memory import Memory
from .tools import ActionError, Toolbox

SYSTEM = ("You are an edge controller. Given sensor readings and recent events, choose exactly one tool call.\n"
          "Rules: if soil_moisture < 30 turn the pump on; if tank_level < 10 log an alert and keep the pump off;\n"
          "if temperature > 40 log an alert; otherwise noop.\n"
          'Answer ONLY with JSON: {"tool": <name>, "args": {...}}.\nTools:\n')


@dataclass
class StepResult:
    action: Optional[dict]
    valid: bool
    result: Optional[str]
    error: Optional[str]
    latency_s: float
    raw: str
    source: str = "local"


class Agent:
    def __init__(self, backend, toolbox: Toolbox, memory: Memory, sensors,
                 cloud_fallback: Optional[Callable[[str], str]] = None, use_cloud: bool = False,
                 max_tokens: int = 64, seed: int = 0):
        self.backend, self.tools, self.memory, self.sensors = backend, toolbox, memory, sensors
        self.cloud_fallback, self.use_cloud = cloud_fallback, use_cloud   # off by default
        self.max_tokens, self.seed = max_tokens, seed

    def build_prompt(self) -> str:
        recent = self.memory.recent(3)
        return (SYSTEM + self.tools.describe() + "\n\nRecent events: " + json.dumps(recent)
                + "\nSensors: " + json.dumps(self.sensors.snapshot()) + "\nAction:")

    def step(self) -> StepResult:
        prompt = self.build_prompt()                      # sense
        t0 = time.perf_counter()
        gen = self.backend.generate(prompt, max_tokens=self.max_tokens, temperature=0.0,
                                    seed=self.seed, json_schema=self.tools.json_schema())   # plan
        raw, source = gen.text, "local"
        action = None
        try:
            action = json.loads(raw)
            result = self.tools.execute(action)             # validate + act
            res = StepResult(action, True, str(result), None, 0.0, raw, source)
        except (json.JSONDecodeError, ActionError) as e:
            if self.use_cloud and self.cloud_fallback:      # explicit opt-in only
                raw = self.cloud_fallback(prompt)
                try:
                    action = json.loads(raw)
                    res = StepResult(action, True, str(self.tools.execute(action)), None, 0.0, raw, "cloud")
                except (json.JSONDecodeError, ActionError) as e2:
                    res = StepResult(action, False, None, str(e2), 0.0, raw, "cloud")
            else:
                res = StepResult(action if isinstance(action, dict) else None, False, None, str(e), 0.0, raw)
        res.latency_s = time.perf_counter() - t0
        self.memory.add("step", {"sensors": self.sensors.snapshot(), "action": res.action,
                                 "valid": res.valid, "error": res.error})
        return res


def cloud_stub(prompt: str) -> str:
    raise NotImplementedError("Cloud fallback is a stub and is disabled by default.")
