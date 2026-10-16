"""One command: python -m bench.run_all  (real, on your PC)   |   python -m bench.run_all --mock  (dummy plumbing check)"""
from __future__ import annotations

import argparse
import json
import sys

from ecaps.power import PowerManager
from ecaps.model_manager import CATALOG, choose, load_config
from bench.preflight import render, run_preflight
from bench import b1_overhead, b2_autofit, b3_offline, b4_power, figures, summary
from bench.common import MockRig, RealRig, env_for, out_dir, save_result


EXPERIMENTS = ("b1", "b2", "b3", "b4")


def parse_only(only: str) -> list[str]:
    sel = list(EXPERIMENTS) if only in ("", "all") else [x.strip().lower() for x in only.split(",")]
    bad = [x for x in sel if x not in EXPERIMENTS]
    if bad:
        raise SystemExit(f"unknown experiment(s) {bad}; choose from {EXPERIMENTS}")
    return sel


def required_tiers(only: str, quant: str = "q4"):
    """Model tiers needed by the selected experiments (so a partial run only needs the models it uses)."""
    sel = parse_only(only)
    names: set[str] = set()
    small = min(CATALOG, key=lambda t: t.params_b).name
    if "b1" in sel or "b3" in sel:
        names.add(small)
    if "b2" in sel:
        names |= {t.name for t in CATALOG}
    if "b4" in sel:
        pm = PowerManager(load_config()["budget_gb"], 1, quant)
        names |= {pm.tier_for("eco"), pm.tier_for("normal")}
    return [t for t in CATALOG if t.name in names]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mock", action="store_true", help="DUMMY run with MockBackend -> results_dummy/")
    ap.add_argument("--repeats", type=int, default=5)
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--quant", default="q4")
    ap.add_argument("--only", default="all", help="comma list of b1,b2,b3,b4 to run (default all). Results of earlier runs are kept.")
    ap.add_argument("--llama-server", help="path to the llama-server binary (else $LLAMA_SERVER, else bin/)")
    ap.add_argument("--models-dir", default="models")
    ap.add_argument("--b3-tier", help="model tier name for B3 (default: smallest tier)")
    a = ap.parse_args(argv)
    sel = parse_only(a.only)
    if a.repeats < 5 and not a.mock:
        print("Refusing: the brief requires at least 5 repeats.", file=sys.stderr); return 2

    if a.mock:
        from bench.mock_responder import responder
        rig = MockRig(responder)
    else:
        rig = RealRig(a.llama_server, a.models_dir, a.quant)
        checks, ok = run_preflight(rig, required_tiers(a.only, a.quant))
        print(render(checks, ok), file=sys.stdout if ok else sys.stderr)
        if not ok:
            print("Cannot run real benchmarks yet. See docs/MODELS.md and docs/RUN_ON_PC.md. Nothing was downloaded.",
                  file=sys.stderr)
            return 3

    env = env_for(a.mock)
    (out_dir(a.mock) / "environment.json").write_text(json.dumps(env, indent=2))
    tier = a.b3_tier or min(CATALOG, key=lambda t: t.params_b).name
    if "b1" in sel:
        save_result("b1_overhead", b1_overhead.run(rig, a.repeats, threads=a.threads), a.mock)
    if "b2" in sel:
        save_result("b2_autofit", b2_autofit.run(rig, repeats=a.repeats, threads=a.threads), a.mock)
    if "b3" in sel:
        save_result("b3_offline", b3_offline.run(rig, a.repeats, a.threads, tier), a.mock)
    power = PowerManager(load_config()["budget_gb"], env["physical_cores"] or env["logical_threads"], a.quant)
    if "b4" in sel:
        save_result("b4_power", b4_power.run(rig, power, a.repeats), a.mock)
    figures.make_all(a.mock)
    print("summary:", summary.write(a.mock))
    return 0


if __name__ == "__main__":
    sys.exit(main())
