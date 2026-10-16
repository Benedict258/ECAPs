"""Model manager: pick the largest model tier that fits a software memory budget.

Estimate (from the brief): weights_GB = params_B * bytes_per_weight
  (16-bit=2, 8-bit=1, 4-bit=0.5), x1.25 for runtime/KV overhead, + 1 GB OS headroom.
The budget is a SOFTWARE setting; it does not change real RAM.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict

BYTES_PER_WEIGHT = {"q4": 0.5, "q8": 1.0, "f16": 2.0}
OVERHEAD = 1.25
OS_HEADROOM_GB = 1.0


@dataclass(frozen=True)
class ModelTier:
    name: str
    params_b: float
    hf_repo: str
    licence: str          # per the model card, checked 17 Oct 2026 (see docs/MODELS.md); GGUF conversion repos not checked


# Tiers ~1.5B / ~3.8B / ~7.6B. Licences: see docs/MODELS.md for sources and check date.
CATALOG = [
    ModelTier("qwen2.5-1.5b-instruct", 1.5, "Qwen/Qwen2.5-1.5B-Instruct-GGUF", "Apache-2.0"),
    ModelTier("phi-3.5-mini-instruct", 3.8, "bartowski/Phi-3.5-mini-instruct-GGUF", "MIT"),
    ModelTier("qwen2.5-7b-instruct", 7.6, "Qwen/Qwen2.5-7B-Instruct-GGUF", "Apache-2.0"),
]


def required_gb(tier: ModelTier, quant: str = "q4") -> dict:
    weights = tier.params_b * BYTES_PER_WEIGHT[quant]
    return {"weights_gb": weights, "with_overhead_gb": weights * OVERHEAD,
            "required_gb": weights * OVERHEAD + OS_HEADROOM_GB}


def choose(budget_gb: float, quant: str = "q4", catalog: list[ModelTier] | None = None) -> dict:
    catalog = sorted(catalog or CATALOG, key=lambda t: t.params_b)
    rows, chosen = [], None
    for t in catalog:
        r = required_gb(t, quant)
        fits = r["required_gb"] <= budget_gb
        rows.append({"tier": t.name, "required_gb": round(r["required_gb"], 2), "fits": fits})
        if fits:
            chosen = t
    if chosen is None:
        reason = (f"No tier fits {budget_gb} GB at {quant}: smallest ({catalog[0].name}) needs "
                  f"{rows[0]['required_gb']} GB.")
        return {"budget_gb": budget_gb, "quant": quant, "chosen": None, "reason": reason, "considered": rows}
    r = required_gb(chosen, quant)
    reason = (f"{chosen.name} ({chosen.params_b}B, {quant}): weights {r['weights_gb']:.2f} GB "
              f"x{OVERHEAD} overhead = {r['with_overhead_gb']:.2f} GB, + {OS_HEADROOM_GB} GB OS headroom "
              f"= {r['required_gb']:.2f} GB <= budget {budget_gb} GB. Largest tier that fits.")
    return {"budget_gb": budget_gb, "quant": quant, "chosen": asdict(chosen), "reason": reason,
            "estimated_required_gb": round(r["required_gb"], 2), "considered": rows,
            "note": "Budget is a software setting, not a change to physical RAM."}


def load_config(path: str = "ecaps.config.json") -> dict:
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return {"budget_gb": 4, "quant": "q4"}


def main(argv=None):
    cfg = load_config()
    ap = argparse.ArgumentParser(description="Choose the model tier that fits a memory budget.")
    ap.add_argument("--budget-gb", type=float, default=cfg["budget_gb"])
    ap.add_argument("--quant", choices=BYTES_PER_WEIGHT, default=cfg["quant"])
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    res = choose(a.budget_gb, a.quant)
    print(json.dumps(res, indent=2) if a.json else res["reason"])


if __name__ == "__main__":
    main()
