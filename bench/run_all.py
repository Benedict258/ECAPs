"""One command: python -m bench.run_all  (real, on your PC)   |   python -m bench.run_all --mock  (dummy plumbing check)"""
from __future__ import annotations

import argparse
import json
import sys

from ecaps.model_manager import CATALOG, choose, load_config
from bench import b1_overhead, b2_autofit, b3_offline, figures, summary
from bench.common import MockRig, RealRig, env_for, out_dir, save_result


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mock", action="store_true", help="DUMMY run with MockBackend -> results_dummy/")
    ap.add_argument("--repeats", type=int, default=5)
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--quant", default="q4")
    a = ap.parse_args(argv)
    if a.repeats < 5 and not a.mock:
        print("Refusing: the brief requires at least 5 repeats.", file=sys.stderr); return 2

    if a.mock:
        from bench.mock_responder import responder
        rig = MockRig(responder)
    else:
        rig = RealRig(quant=a.quant)
        miss = rig.missing(CATALOG)
        if miss:
            print("Cannot run real benchmarks yet. Missing:\n  " + "\n  ".join(miss) +
                  "\nSee docs/MODELS.md. Nothing was downloaded.", file=sys.stderr); return 3

    env = env_for(a.mock)
    (out_dir(a.mock) / "environment.json").write_text(json.dumps(env, indent=2))
    tier = choose(load_config()["budget_gb"])["chosen"]["name"]
    save_result("b1_overhead", b1_overhead.run(rig, a.repeats, threads=a.threads), a.mock)
    save_result("b2_autofit", b2_autofit.run(rig, repeats=a.repeats, threads=a.threads), a.mock)
    save_result("b3_offline", b3_offline.run(rig, a.repeats, a.threads, tier), a.mock)
    figures.make_all(a.mock)
    print("summary:", summary.write(a.mock))
    return 0


if __name__ == "__main__":
    sys.exit(main())
