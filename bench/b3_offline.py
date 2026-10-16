"""B3: 20-task agent loop, network allowed vs outbound blocked (loopback to llama-server allowed)."""
from __future__ import annotations

import socket
from contextlib import contextmanager

from ecaps.agent import Agent
from ecaps.devices import SimulatedSensors
from ecaps.memory import Memory
from ecaps.model_manager import CATALOG
from ecaps.tools import Toolbox
from bench.common import summarize
from bench.tasks import TASKS, is_correct

LOOPBACK = {"127.0.0.1", "::1", "localhost"}


@contextmanager
def block_outbound(attempts: list):
    real = socket.socket.connect

    def guard(self, addr):
        host = addr[0] if isinstance(addr, tuple) else str(addr)
        if self.family == getattr(socket, "AF_UNIX", None) or host in LOOPBACK:
            return real(self, addr)
        attempts.append(host)
        raise OSError(f"outbound connection blocked by bench guard: {host}")
    socket.socket.connect = guard
    try:
        yield
    finally:
        socket.socket.connect = real


def _run_tasks(backend):
    out = []
    for sensors_vals, expected in TASKS:
        s = SimulatedSensors(sensors_vals)
        mem = Memory(":memory:")           # fresh memory per task keeps tasks independent/deterministic
        r = Agent(backend, Toolbox(s), mem, s).step()
        out.append({"correct": is_correct(r.action, expected), "valid": r.valid, "latency_s": r.latency_s,
                    "action": r.action, "expected": list(expected)})
        mem.close()
    return out


def run(rig, repeats: int = 5, threads: int = 4, tier_name: str | None = None) -> dict:
    tier = next((t for t in CATALOG if t.name == tier_name), CATALOG[0])
    s = rig.start(tier, threads)
    modes = {}
    try:
        s.backend.generate("warm up", 4, 0.0, 0)
        for mode in ("network_allowed", "network_blocked"):
            attempts, runs = [], []
            for _ in range(repeats):
                if mode == "network_blocked":
                    with block_outbound(attempts):
                        runs.append(_run_tasks(s.backend))
                else:
                    runs.append(_run_tasks(s.backend))
            correct = [sum(t["correct"] for t in r) for r in runs]
            modes[mode] = {"tasks": len(TASKS), "correct_per_repeat": correct, "correct": summarize(correct),
                           "valid_actions_per_repeat": [sum(t["valid"] for t in r) for r in runs],
                           "latency_s": summarize([t["latency_s"] for r in runs for t in r]),
                           "outbound_attempts": attempts if mode == "network_blocked" else None,
                           "failures_first_repeat": [{"task": i, **t} for i, t in enumerate(runs[0]) if not t["correct"]],
                           "raw_runs": runs}
    finally:
        s.stop()
    return {"model": tier.name, "threads": threads, "repeats": repeats, "modes": modes,
            "note": "'network_allowed' means no guard (the agent still never uses the network; cloud fallback is off)."}
