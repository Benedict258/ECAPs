"""A Node ties together power manager, backend, agent, memory and metrics (used by the management API)."""
from __future__ import annotations

import threading
import time
from typing import Callable

from .agent import Agent
from .devices import SimulatedSensors
from .memory import Memory
from .model_manager import CATALOG, choose
from .power import ModePlan, PowerManager
from .tools import Toolbox


class Node:
    """backend_factory(plan) -> (backend, closer). Called again when a power change alters the plan."""

    def __init__(self, backend_factory: Callable, power: PowerManager, sensors=None,
                 memory: Memory | None = None, battery_pct: float = 100.0, solar: bool = False):
        self.factory, self.power = backend_factory, power
        self.sensors = sensors or SimulatedSensors()
        self.memory = memory or Memory(":memory:")
        self.toolbox = Toolbox(self.sensors)
        self.started = time.time()
        self.lock = threading.Lock()
        self.battery_pct, self.solar = battery_pct, solar
        self.metrics = {"steps": 0, "valid_actions": 0, "invalid_actions": 0, "mode_switches": 0,
                        "latency_s_total": 0.0, "tokens_total": 0, "last_tokens_per_s": None}
        self._backend = self._closer = None
        self.plan: ModePlan | None = None
        self._apply(self.power.plan_for(battery_pct, solar))

    def _apply(self, plan: ModePlan):
        if plan != self.plan:
            if self._closer:
                self._closer()
            self._backend, self._closer = self.factory(plan)
            if self.plan is not None:
                self.metrics["mode_switches"] += 1
            self.plan = plan
            self.agent = Agent(self._backend, self.toolbox, self.memory, self.sensors, max_tokens=plan.max_tokens)

    def set_power(self, battery_pct: float, solar: bool = False) -> ModePlan:
        self.battery_pct, self.solar = battery_pct, solar
        self._apply(self.power.plan_for(battery_pct, solar))
        return self.plan

    def step(self):
        r = self.agent.step()
        with self.lock:
            m = self.metrics
            m["steps"] += 1
            m["valid_actions" if r.valid else "invalid_actions"] += 1
            m["latency_s_total"] += r.latency_s
            m["tokens_total"] += r.n_tokens
            m["last_tokens_per_s"] = r.tokens_per_s
        return r

    def close(self):
        if self._closer:
            self._closer()
