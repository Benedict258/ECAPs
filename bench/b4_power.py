"""B4: eco / normal / boost on the same 20-task set. CPU-seconds per task is an energy PROXY, not energy."""
from __future__ import annotations

import time

from ecaps.agent import Agent
from ecaps.devices import SimulatedSensors
from ecaps.memory import Memory
from ecaps.model_manager import CATALOG
from ecaps.power import MODES, PowerManager
from ecaps.tools import Toolbox
from bench.common import summarize
from bench.tasks import TASKS, is_correct


def run(rig, power: PowerManager, repeats: int = 5) -> dict:
    out = {}
    for mode in MODES:
        plan = power.plan(mode)
        tier = next(t for t in CATALOG if t.name == plan.tier)
        s = rig.start(tier, plan.threads, plan.ctx)
        try:
            s.backend.generate("warm up", 4, 0.0, 0)
            walls, cpu_per_task, correct, tps, lat = [], [], [], [], []
            for _ in range(repeats):
                c0, t0, ok = s.cpu_seconds(), time.perf_counter(), 0
                for vals, expected in TASKS:
                    sensors, mem = SimulatedSensors(vals), Memory(":memory:")
                    r = Agent(s.backend, Toolbox(sensors), mem, sensors, max_tokens=plan.max_tokens).step()
                    ok += is_correct(r.action, expected)
                    if r.tokens_per_s > 0: tps.append(r.tokens_per_s)
                    lat.append(r.latency_s); mem.close()
                walls.append(time.perf_counter() - t0)
                cpu_per_task.append((s.cpu_seconds() - c0) / len(TASKS))
                correct.append(ok)
        finally:
            s.stop()
        out[mode] = {"plan": plan.as_dict(), "tasks": len(TASKS), "correct_per_repeat": correct,
                     "correct": summarize(correct), "wall_time_s": summarize(walls),
                     "cpu_seconds_per_task": summarize(cpu_per_task),
                     "tokens_per_s": summarize(tps) if tps else None, "latency_s": summarize(lat)}
    return {"repeats": repeats, "modes": out,
            "note": "cpu_seconds_per_task = user+system CPU time of llama-server + this client process, divided by tasks. "
                    "It is an energy PROXY only; no watts were measured and no energy saving is claimed. "
                    "tokens_per_s is per-step generation speed over short JSON actions (few tokens), so it is noisy."}
