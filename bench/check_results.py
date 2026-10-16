"""Pre-print check for REAL results: `python -m bench.check_results`. Read-only. Exit code 0 only if everything looks print-ready.
It checks bookkeeping (DUMMY flags, files present, commit hash); it cannot judge whether the results are good, and a person still
has to look at every figure."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from ecaps.environment import commit_hash

ROOT = Path(__file__).resolve().parent.parent
FIGS = {"b1_overhead": "F1_overhead", "b2_autofit": "F2_autofit", "b3_offline": "F3_offline", "b4_power": "F4_power_modes"}


def check(results: Path | None = None) -> list[tuple[str, str, str]]:
    r = results or ROOT / "results"
    out: list[tuple[str, str, str]] = []
    add = lambda s, n, d: out.append((s, n, d))
    if not r.is_dir():
        return [("FAIL", "results directory", f"{r} does not exist: run bench.run_all on the real PC first")]
    env_p = r / "environment.json"
    if not env_p.exists():
        add("FAIL", "environment.json", "missing")
    else:
        env = json.loads(env_p.read_text())
        add("FAIL" if "warning" in env else "PASS", "environment.json", env.get("cpu_model", "?") if "warning" not in env else env["warning"])
        head = commit_hash()
        add("PASS" if env.get("runtime_commit") == head else "WARN", "commit hash",
            f"results recorded {env.get('runtime_commit')}, repo is at {head}" + ("" if env.get("runtime_commit") == head else " (results are from a different commit)"))
    found = 0
    for key, fig in FIGS.items():
        p = r / f"{key}.json"
        if not p.exists():
            add("WARN", key, "no results file: that poster slot stays empty (summary.md says 'not run')")
            continue
        found += 1
        d = json.loads(p.read_text())
        add("FAIL" if d.get("dummy") else "PASS", key, "marked DUMMY" if d.get("dummy") else "real results file")
        ok = all((r / "figures" / f"{fig}.{e}").exists() for e in ("png", "svg"))
        add("PASS" if ok else "FAIL", fig, "PNG and SVG present" if ok else "figure missing: run python -m bench.figures")
    if found == 0:
        add("FAIL", "results", "no experiment results found")
    s = r / "summary.md"
    if not s.exists():
        add("FAIL", "summary.md", "missing")
    else:
        add("FAIL" if "DUMMY" in s.read_text() else "PASS", "summary.md", "contains DUMMY banner" if "DUMMY" in s.read_text() else "no DUMMY banner")
    return out


def main(argv=None) -> int:
    rows = check(Path(argv[0]) if argv else None)
    for s, n, d in rows:
        print(f"[{s}] {n}: {d}")
    ok = all(s != "FAIL" for s, _, _ in rows)
    print("RESULT:", "PASS (still look at every figure and read summary.md before printing)" if ok else "FAIL (do not print)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
