"""Backend interface. Real inference = llama.cpp (llama-server over HTTP).
MockBackend exists only for development/tests and is always flagged is_mock."""
from __future__ import annotations

import json
import time
import urllib.request
from dataclasses import dataclass, field
from typing import Optional, Protocol


@dataclass
class GenResult:
    text: str
    n_tokens: int
    ttft_s: float          # time to first token
    total_s: float
    is_mock: bool = False

    @property
    def tokens_per_s(self) -> float:
        dur = max(self.total_s - self.ttft_s, 1e-9)
        return max(self.n_tokens - 1, 0) / dur if self.n_tokens > 1 else 0.0


class Backend(Protocol):
    is_mock: bool

    def generate(self, prompt: str, max_tokens: int = 64, temperature: float = 0.0,
                 seed: int = 0, json_schema: Optional[dict] = None,
                 ignore_eos: bool = False) -> GenResult: ...


class MockBackend:
    """Deterministic fake. Its timings are NOT measurements of anything real."""
    is_mock = True

    def __init__(self, responder=None, tokens_per_s: float = 2000.0):
        self.responder = responder or (lambda prompt: "mock output " * 8)
        self.tps = tokens_per_s
        self.calls: list[str] = []

    def generate(self, prompt, max_tokens=64, temperature=0.0, seed=0, json_schema=None, ignore_eos=False):
        self.calls.append(prompt)
        t0 = time.perf_counter()
        text = self.responder(prompt)
        words = text.split()
        n = min(max(len(words), 1), max_tokens)
        text = " ".join(words[:n]) if json_schema is None else text
        if ignore_eos:
            n = max_tokens
        time.sleep(n / self.tps)
        total = time.perf_counter() - t0
        return GenResult(text=text, n_tokens=n, ttft_s=total / max(n, 1),
                         total_s=total, is_mock=True)


class LlamaServerBackend:
    """Talks to a running llama.cpp `llama-server` over local HTTP (streaming)."""
    is_mock = False

    def __init__(self, url: str = "http://127.0.0.1:8080", timeout: float = 300.0):
        self.url = url.rstrip("/")
        self.timeout = timeout

    def generate(self, prompt, max_tokens=64, temperature=0.0, seed=0, json_schema=None, ignore_eos=False):
        body = {"prompt": prompt, "n_predict": max_tokens, "temperature": temperature,
                "seed": seed, "stream": True, "cache_prompt": False, "ignore_eos": ignore_eos}
        if json_schema is not None:
            body["json_schema"] = json_schema
        req = urllib.request.Request(self.url + "/completion", json.dumps(body).encode(),
                                     {"Content-Type": "application/json"})
        t0 = time.perf_counter()
        ttft = None
        n = 0
        parts: list[str] = []
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            for raw in resp:
                line = raw.decode().strip()
                if not line.startswith("data:"):
                    continue
                ev = json.loads(line[5:])
                if ev.get("content"):
                    if ttft is None:
                        ttft = time.perf_counter() - t0
                    parts.append(ev["content"])
                if ev.get("stop"):
                    n = ev.get("tokens_predicted", n)
                    break
        total = time.perf_counter() - t0
        return GenResult("".join(parts), n or len(parts), ttft if ttft is not None else total, total)

    def healthy(self) -> bool:
        try:
            with urllib.request.urlopen(self.url + "/health", timeout=3) as r:
                return r.status == 200
        except Exception:
            return False
