"""Minimal direct llama-server client for B1's baseline. Deliberately independent of the ecaps package."""
import http.client
import json
import time
from urllib.parse import urlparse

from ecaps.backend import GenResult


def raw_generate(url: str, prompt: str, n: int, seed: int) -> GenResult:
    u = urlparse(url)
    c = http.client.HTTPConnection(u.hostname, u.port, timeout=600)
    body = json.dumps({"prompt": prompt, "n_predict": n, "temperature": 0, "seed": seed,
                       "stream": True, "cache_prompt": False, "ignore_eos": True})
    t0 = time.perf_counter()
    c.request("POST", "/completion", body, {"Content-Type": "application/json"})
    r = c.getresponse()
    ttft, toks, text = None, 0, []
    for line in r:
        if not line.startswith(b"data:"):
            continue
        ev = json.loads(line[5:])
        if ev.get("content"):
            ttft = ttft or time.perf_counter() - t0
            text.append(ev["content"])
        if ev.get("stop"):
            toks = ev.get("tokens_predicted", len(text))
            break
    total = time.perf_counter() - t0
    c.close()
    return GenResult("".join(text), toks or len(text), ttft or total, total)
