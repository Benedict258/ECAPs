"""Auto-detect the machine. Nothing here is assumed."""
from __future__ import annotations

import datetime
import json
import os
import platform
import subprocess
from pathlib import Path

import psutil


def _cpu_model() -> str:
    try:
        if platform.system() == "Windows":
            import winreg
            k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                               r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
            return winreg.QueryValueEx(k, "ProcessorNameString")[0].strip()
        if platform.system() == "Linux":
            for line in Path("/proc/cpuinfo").read_text().splitlines():
                if line.lower().startswith("model name"):
                    return line.split(":", 1)[1].strip()
        if platform.system() == "Darwin":
            return subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"],
                                           text=True).strip()
    except Exception:
        pass
    return platform.processor() or "unknown"


def commit_hash(repo: Path | None = None) -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"],
                                       cwd=repo or Path(__file__).resolve().parent.parent,
                                       text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return "unknown"


def capture() -> dict:
    vm = psutil.virtual_memory()
    return {
        "cpu_model": _cpu_model(),
        "physical_cores": psutil.cpu_count(logical=False),
        "logical_threads": psutil.cpu_count(logical=True),
        "ram_total_gb": round(vm.total / 2**30, 2),
        "ram_available_gb": round(vm.available / 2**30, 2),
        "os": f"{platform.system()} {platform.release()} ({platform.version()})",
        "machine": platform.machine(),
        "python": platform.python_version(),
        "accelerator": "none (CPU-only inference)",
        "date": datetime.date.today().isoformat(),
        "runtime_commit": commit_hash(),
        "note": "Stand-in reference machine. Not ECAPs hardware.",
    }


def footer_line(env: dict, models: list[str] | None = None) -> str:
    s = (f"Measured on: {env['cpu_model']}, {env['ram_total_gb']} GB RAM, {env['os'].split(' (')[0]}, "
         f"CPU-only | {env['date']} | commit {env['runtime_commit']}")
    if models:
        s += " | models: " + ", ".join(models)
    return s


def save(path: str | os.PathLike = "results/environment.json") -> dict:
    env = capture()
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(env, indent=2))
    return env


if __name__ == "__main__":
    import sys
    print(json.dumps(save(*(sys.argv[1:2])), indent=2))
