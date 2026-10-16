"""Shared bench plumbing: stats, result I/O, and the rigs (real llama-server vs labelled mock)."""
from __future__ import annotations

import json
import os
import statistics as st
import subprocess
import threading
import time
from pathlib import Path

import psutil

from ecaps import environment
from ecaps.backend import LlamaServerBackend, MockBackend
from ecaps.model_manager import CATALOG, ModelTier

ROOT = Path(__file__).resolve().parent.parent
GB = 2**30


def summarize(xs: list[float]) -> dict:
    xs = [float(x) for x in xs]
    return {"n": len(xs), "mean": st.fmean(xs), "std": st.stdev(xs) if len(xs) > 1 else 0.0,
            "min": min(xs), "max": max(xs), "raw": xs}


def out_dir(mock: bool) -> Path:
    d = ROOT / ("results_dummy" if mock else "results")
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_result(name: str, data: dict, mock: bool) -> Path:
    data = {"dummy": mock, "experiment": name, **data}
    if mock:
        data["warning"] = "DUMMY DATA from MockBackend. Not a measurement of anything."
    p = out_dir(mock) / f"{name}.json"
    p.write_text(json.dumps(data, indent=2))
    return p


def load_result(name: str, mock: bool) -> dict | None:
    p = out_dir(mock) / f"{name}.json"
    return json.loads(p.read_text()) if p.exists() else None


def gguf_path(tier: ModelTier, quant: str = "q4", models_dir: str = "models") -> Path:
    suffix = {"q4": "Q4_K_M", "q8": "Q8_0"}[quant]
    return ROOT / models_dir / f"{tier.name}-{suffix}.gguf"


class _RssWatcher(threading.Thread):
    def __init__(self, procs):
        super().__init__(daemon=True)
        self.procs, self.peak, self._halt = procs, 0, threading.Event()

    def run(self):
        while not self._halt.is_set():
            try:
                self.peak = max(self.peak, sum(p.memory_info().rss for p in self.procs()))
            except psutil.Error:
                pass
            time.sleep(0.05)

    def stop(self): self._halt.set()


class Session:
    """A loaded model + a way to call it directly and through the runtime + peak RSS tracking."""
    def __init__(self, tier, backend, direct, procs, closer=lambda: None):
        self.tier, self.backend, self.direct, self._closer = tier, backend, direct, closer
        self._watch = _RssWatcher(procs)
        self._watch.start()

    def reset_peak(self): self._watch.peak = 0
    def peak_rss_gb(self) -> float: return self._watch.peak / GB

    def stop(self):
        self._watch.stop()
        self._closer()


class MockRig:
    """Plumbing check only. RSS reported is this Python process's, which says nothing about any model."""
    is_mock = True
    name = "mock"

    def __init__(self, responder=None):
        self.responder = responder

    def start(self, tier: ModelTier, threads: int, ctx: int = 2048) -> Session:
        be = MockBackend(self.responder)
        me = psutil.Process()
        return Session(tier, be, lambda p, n, seed: be.generate(p, n, 0.0, seed, ignore_eos=True), lambda: [me])


class RealRig:
    """Launches llama.cpp `llama-server` (CPU) for a tier and measures it. Run on the owner's PC only."""
    is_mock = False
    name = "llama-server"

    def __init__(self, binary: str | None = None, models_dir: str = "models", quant: str = "q4", port: int = 8089):
        self.binary = binary or os.environ.get("LLAMA_SERVER", str(ROOT / "bin" / "llama-server"))
        self.models_dir, self.quant, self.port = models_dir, quant, port

    def missing(self, tiers) -> list[str]:
        miss = [] if Path(self.binary).exists() else [f"llama-server binary: {self.binary}"]
        return miss + [str(gguf_path(t, self.quant, self.models_dir)) for t in tiers
                       if not gguf_path(t, self.quant, self.models_dir).exists()]

    def start(self, tier: ModelTier, threads: int, ctx: int = 2048) -> Session:
        model = gguf_path(tier, self.quant, self.models_dir)
        proc = subprocess.Popen([self.binary, "-m", str(model), "-t", str(threads), "-c", str(ctx),
                                 "--host", "127.0.0.1", "--port", str(self.port), "--parallel", "1"],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        be = LlamaServerBackend(f"http://127.0.0.1:{self.port}")
        for _ in range(600):
            if proc.poll() is not None:
                raise RuntimeError("llama-server exited early")
            if be.healthy():
                break
            time.sleep(0.5)
        else:
            proc.kill()
            raise RuntimeError("llama-server did not become healthy")
        from bench.raw_llama import raw_generate
        sp = psutil.Process(proc.pid)
        me = psutil.Process()

        def closer():
            proc.terminate()
            try: proc.wait(20)
            except subprocess.TimeoutExpired: proc.kill()
        return Session(tier, be, lambda p, n, seed: raw_generate(f"http://127.0.0.1:{self.port}", p, n, seed),
                       lambda: [sp, me], closer)


def tier_by_name(name: str) -> ModelTier:
    return next(t for t in CATALOG if t.name == name)


def env_for(mock: bool) -> dict:
    env = environment.capture()
    if mock:
        env["warning"] = "DUMMY: captured inside a cloud container for a mock run; NOT the owner's PC."
    return env
