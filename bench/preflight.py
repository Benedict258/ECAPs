"""Preflight for REAL benchmark runs: `python -m bench.preflight`. Also runs at the start of
`python -m bench.run_all` (real mode). Checks only; it NEVER downloads anything."""
from __future__ import annotations

import argparse
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

import psutil

from ecaps.model_manager import CATALOG, required_gb
from bench.common import GB, ROOT, RealRig, gguf_path

MIN_FREE_DISK_GB = 2.0
BIG_BUDGET_GB = 7.0          # B2's largest software budget
EST_BYTES_PER_PARAM_Q4 = 0.6  # rough GGUF Q4_K_M size estimate, labelled "est." wherever shown


@dataclass
class Check:
    name: str
    status: str    # PASS | FAIL | WARN
    detail: str


def _gib(b: float) -> str: return f"{b / GB:.2f} GB"


def run_preflight(rig: RealRig | None = None, free_disk_gb: float | None = None,
                  ram_available_gb: float | None = None, ram_total_gb: float | None = None,
                  swap_used_gb: float | None = None) -> tuple[list[Check], bool]:
    """Returns (checks, ok). ok is False if any check is FAIL (WARN does not fail)."""
    rig = rig or RealRig()
    checks: list[Check] = []
    add = lambda n, s, d: checks.append(Check(n, s, d))

    add("Python >= 3.11", "PASS" if sys.version_info >= (3, 11) else "FAIL", sys.version.split()[0])

    b = Path(rig.binary)
    if b.is_file():
        add("llama-server binary", "PASS", f"{b} ({_gib(b.stat().st_size)})")
    else:
        add("llama-server binary", "FAIL", f"not found at {b} (put it at bin/llama-server[.exe] or set LLAMA_SERVER)")

    total_est = 0.0
    for t in sorted(CATALOG, key=lambda t: t.params_b):
        p = gguf_path(t, rig.quant, rig.models_dir)
        est = t.params_b * EST_BYTES_PER_PARAM_Q4 * 1e9
        total_est += est
        if not p.is_file():
            add(f"model {t.name}", "FAIL", f"missing: {p} (est. {est / 1e9:.1f} GB, see docs/MODELS.md)")
            continue
        with open(p, "rb") as f:
            magic = f.read(4)
        if magic != b"GGUF":
            add(f"model {t.name}", "FAIL", f"{p} is not a valid GGUF file (bad header); re-download may be needed")
        else:
            add(f"model {t.name}", "PASS", f"{p} ({_gib(p.stat().st_size)})")

    free = free_disk_gb if free_disk_gb is not None else shutil.disk_usage(ROOT).free / GB
    add("free disk space", "PASS" if free >= MIN_FREE_DISK_GB else "FAIL",
        f"{free:.1f} GB free (need >= {MIN_FREE_DISK_GB:.0f} GB for results/logs; models are separate)")

    vm = psutil.virtual_memory()
    avail = ram_available_gb if ram_available_gb is not None else vm.available / GB
    total = ram_total_gb if ram_total_gb is not None else vm.total / GB
    big = max(CATALOG, key=lambda t: t.params_b)
    need_big = required_gb(big, rig.quant)["required_gb"]
    if avail >= need_big:
        add("available RAM for the 7 GB budget run", "PASS",
            f"{avail:.1f} of {total:.1f} GB available; largest model est. needs {need_big:.1f} GB")
    else:
        add("available RAM for the 7 GB budget run", "WARN",
            f"only {avail:.1f} of {total:.1f} GB available; largest model est. needs {need_big:.1f} GB. "
            "Close browsers and other apps first, or the naive-7B test may swap and give poor/unrepresentative numbers")
    if total < BIG_BUDGET_GB:
        add("total RAM vs 7 GB budget", "WARN",
            f"machine has {total:.1f} GB total; a 7 GB software budget cannot be honestly exercised, results will say what happened")

    swap = swap_used_gb if swap_used_gb is not None else psutil.swap_memory().used / GB
    if swap > 0.5:
        add("swap in use", "WARN", f"{swap:.1f} GB swap already in use; restart or close apps before benchmarking")
    else:
        add("swap in use", "PASS", f"{swap:.2f} GB")

    return checks, all(c.status != "FAIL" for c in checks)


def render(checks: list[Check], ok: bool) -> str:
    mark = {"PASS": "[PASS]", "FAIL": "[FAIL]", "WARN": "[WARN]"}
    lines = ["ECAPs preflight (checks only; nothing is downloaded)", ""]
    lines += [f"{mark[c.status]} {c.name}: {c.detail}" for c in checks]
    lines += ["", "Before the 7 GB budget run (B2): close other applications (browser, chat, IDE) and leave the PC idle.",
              "RESULT: " + ("PASS" if ok else "FAIL (fix the [FAIL] items; see docs/RUN_ON_PC.md)")]
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quant", default="q4")
    a = ap.parse_args(argv)
    checks, ok = run_preflight(RealRig(quant=a.quant))
    print(render(checks, ok))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())
