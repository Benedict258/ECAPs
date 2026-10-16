"""B1: runtime overhead vs calling llama-server directly. Same model/prompt/tokens/threads/seed."""
from __future__ import annotations

from ecaps.model_manager import CATALOG
from bench.common import summarize

PROMPT = "Explain in simple terms why irrigation timing matters for crop yield. " * 4


def run(rig, repeats: int = 5, n_tokens: int = 64, threads: int = 4, tier_name: str | None = None) -> dict:
    tier = next((t for t in CATALOG if t.name == tier_name), CATALOG[0])
    s = rig.start(tier, threads)
    try:
        s.direct(PROMPT, n_tokens, 0); s.backend.generate(PROMPT, n_tokens, 0.0, 0, ignore_eos=True)  # warm-up, discarded
        d, r = [], []
        for i in range(repeats):          # interleaved to avoid order/thermal bias
            s.reset_peak(); g = s.direct(PROMPT, n_tokens, 0)
            d.append({"tps": g.tokens_per_s, "ttft": g.ttft_s, "n": g.n_tokens, "peak_rss_gb": s.peak_rss_gb()})
            s.reset_peak(); g = s.backend.generate(PROMPT, n_tokens, 0.0, 0, ignore_eos=True)
            r.append({"tps": g.tokens_per_s, "ttft": g.ttft_s, "n": g.n_tokens, "peak_rss_gb": s.peak_rss_gb()})
    finally:
        s.stop()
    pct = [(a["tps"] - b["tps"]) / a["tps"] * 100 for a, b in zip(d, r) if a["tps"] > 0]
    return {"model": tier.name, "threads": threads, "n_tokens": n_tokens, "repeats": repeats,
            "warmup_runs_discarded": 1,
            "direct": {k: summarize([x[k] for x in d]) for k in ("tps", "ttft", "peak_rss_gb")},
            "runtime": {k: summarize([x[k] for x in r]) for k in ("tps", "ttft", "peak_rss_gb")},
            "token_counts_direct": [x["n"] for x in d], "token_counts_runtime": [x["n"] for x in r],
            "tps_overhead_pct": summarize(pct) if pct else None,
            "note": "Positive overhead % = runtime slower than direct. Both paths hit the same llama-server."}
