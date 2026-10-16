"""B2: memory auto-fit at 2/4/7 GB software budgets vs a naive always-largest-model policy."""
from __future__ import annotations

from ecaps.model_manager import CATALOG, choose
from bench.b1_overhead import PROMPT
from bench.common import summarize


def _measure(rig, tier, threads, repeats, n_tokens):
    s = rig.start(tier, threads)
    try:
        s.direct(PROMPT, 8, 0)  # warm-up
        peaks, tps = [], []
        s.reset_peak()
        for _ in range(repeats):
            g = s.backend.generate(PROMPT, n_tokens, 0.0, 0, ignore_eos=True)
            tps.append(g.tokens_per_s); peaks.append(s.peak_rss_gb())
        return {"peak_rss_gb": summarize(peaks), "tps": summarize(tps)}
    finally:
        s.stop()


def run(rig, budgets=(2, 4, 7), repeats: int = 5, n_tokens: int = 48, threads: int = 4) -> dict:
    largest = max(CATALOG, key=lambda t: t.params_b)
    rows = []
    for b in budgets:
        pick = choose(b)
        row = {"budget_gb": b, "reason": pick["reason"], "estimated_required_gb": pick.get("estimated_required_gb")}
        for label, tier in (("autofit", next((t for t in CATALOG if pick["chosen"] and t.name == pick["chosen"]["name"]), None)),
                            ("naive_largest", largest)):
            if tier is None:
                row[label] = None
                continue
            m = _measure(rig, tier, threads, repeats, n_tokens)
            m.update(model=tier.name, under_budget=m["peak_rss_gb"]["max"] <= b)
            row[label] = m
        rows.append(row)
    return {"repeats": repeats, "threads": threads, "rows": rows,
            "note": "Budget is a SOFTWARE setting, not a change to physical RAM. Peak RSS includes mmap'd model pages "
                    "and the client process; 'under_budget' compares max observed peak RSS to the budget."}
