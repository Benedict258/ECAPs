"""results/summary.md, generated from results JSON only."""
from __future__ import annotations

import json

from bench.common import load_result, out_dir
from ecaps.environment import footer_line


def _f(s, nd=2): return f"{s['mean']:.{nd}f} ± {s['std']:.{nd}f} (min {s['min']:.{nd}f}, max {s['max']:.{nd}f}, n={s['n']})"


def write(mock: bool) -> str:
    env = json.loads((out_dir(mock) / "environment.json").read_text())
    L = []
    if mock:
        L += ["> **DUMMY DATA from MockBackend, generated in a cloud container. NOT measurements. No real model was run. Do not use on the poster.**", ""]
    L += ["# ECAPs Node Runtime: results summary", "", "Research prototype. Stand-in reference machine, not ECAPs hardware.", "",
          f"**{footer_line(env)}**", ""]
    b1, b2, b3, b4 = (load_result(n, mock) for n in ("b1_overhead", "b2_autofit", "b3_offline", "b4_power"))
    if b1:
        o = b1["tps_overhead_pct"]
        L += ["## B1 Overhead vs raw llama-server", f"Model {b1['model']}, {b1['threads']} threads, {b1['n_tokens']} tokens, {b1['repeats']} repeats (+1 discarded warm-up).", "",
              "| metric | raw | via runtime |", "|---|---|---|"]
        for k, lab in (("tps", "tokens/s"), ("ttft", "time to first token (s)"), ("peak_rss_gb", "peak RSS (GB)")):
            L.append(f"| {lab} | {_f(b1['direct'][k], 3)} | {_f(b1['runtime'][k], 3)} |")
        L += ["", f"Overhead (tokens/s, positive = runtime slower): {_f(o, 2)} %", "",
              f"*Caption F1:* Same model, prompt, tokens and threads; both paths call the same llama-server. "
              f"Measured overhead {o['mean']:.1f}% ± {o['std']:.1f}% (n={b1['repeats']}). The runtime wraps llama.cpp; it does not make it faster.", ""]
    if b2:
        L += ["## B2 Memory auto-fit (software budget)", "", "| budget GB | auto-fit model | peak RSS GB | under budget | tok/s | naive largest | naive peak RSS GB | naive under budget |", "|---|---|---|---|---|---|---|---|"]
        for r in b2["rows"]:
            a, n = r["autofit"], r["naive_largest"]
            L.append(f"| {r['budget_gb']} | {a['model'] if a else 'none fits'} | {_f(a['peak_rss_gb'], 2) if a else '-'} | "
                     f"{a['under_budget'] if a else '-'} | {_f(a['tps'], 2) if a else '-'} | {n['model']} | {_f(n['peak_rss_gb'], 2)} | {n['under_budget']} |")
        L += ["", "Manager reasoning:"] + [f"- {r['budget_gb']} GB: {r['reason']}" for r in b2["rows"]]
        L += ["", "*Caption F2:* Budget is a software setting; physical RAM is unchanged. Peak RSS is the maximum observed for the server plus client process "
              "(includes memory-mapped model pages). Dashed line = budget.", ""]
    if b3:
        L += ["## B3 Offline agent loop", f"Model {b3['model']}, 20 tasks x {b3['repeats']} repeats, temperature 0.", "",
              "| mode | correct per repeat | mean correct | latency per task (s) | outbound attempts |", "|---|---|---|---|---|"]
        for k, m in b3["modes"].items():
            L.append(f"| {k} | {m['correct_per_repeat']} / {m['tasks']} | {_f(m['correct'], 2)} | {_f(m['latency_s'], 3)} | "
                     f"{len(m['outbound_attempts']) if m['outbound_attempts'] is not None else 'n/a (not guarded)'} |")
        fails = b3["modes"]["network_blocked"]["failures_first_repeat"]
        L += ["", f"Failures in first blocked repeat ({len(fails)}), kept as-is:"] + [f"- task {f['task']}: expected {f['expected']}, got {f['action']}" for f in fails]
        L += ["", "*Caption F3:* Same task set with and without outbound network. Loopback to the local llama-server is allowed in the blocked mode; any other connection attempt is recorded and refused.", ""]
    if b4:
        L += ["## B4 Power modes", f"20 tasks x {b4['repeats']} repeats per mode. **CPU-seconds is an energy PROXY only; no watts were measured; no energy saving is claimed.**", "",
              "| mode | tier | threads | max tokens | ctx | tokens/s | CPU-s per task | wall time 20 tasks (s) | mean correct |", "|---|---|---|---|---|---|---|---|---|"]
        for k, m in b4["modes"].items():
            p_ = m["plan"]
            L.append(f"| {k} | {p_['tier']} | {p_['threads']} | {p_['max_tokens']} | {p_['ctx']} | {_f(m['tokens_per_s'], 2) if m['tokens_per_s'] else '-'} | "
                     f"{_f(m['cpu_seconds_per_task'], 3)} | {_f(m['wall_time_s'], 2)} | {_f(m['correct'], 2)} / {m['tasks']} |")
        L += ["", "*Caption F4:* Same 20 tasks in each power mode (threads, max output tokens, context size and model tier change by mode; battery level is simulated). "
              "CPU-seconds per task is a proxy for energy, not a measurement of it.", ""]
    missing = []
    for name, res in (("B1 overhead / F1", b1), ("B2 auto-fit / F2", b2), ("B3 offline loop / F3", b3), ("B4 power modes / F4", b4)):
        if not res:
            missing.append(f"- {name}: not run (no results file present).")
    if missing:
        L += ["## Not run"] + missing
    L += ["", "## Unverified or not measured (applies to every run)",
          "- Serial/ESP32 adapter: tested only against an in-memory fake port; the example ESP32 sketch has not been compiled or run.",
          "- MQTT adapter: tested only against an in-memory fake broker; never run against a real broker or device.",
          "- Node discovery and request routing: tested on localhost only (several processes on 127.0.0.1); not on a real LAN; throughput gain not measured.",
          "- Offline-first outbox: cloud sync tested only against a localhost server; the cloud endpoint is a stub, off by default.",
          "- Management API (/status /models /metrics): functional tests only; not benchmarked.",
          "- Model licences: unverified (see docs/MODELS.md).",
          "- Energy: not measured. CPU-seconds is a proxy; no energy saving is claimed.",
          "- docs/NODE_SPEC_PROPOSED.md: proposed arithmetic, not measurements."]
    p = out_dir(mock) / "summary.md"
    p.write_text("\n".join(L) + "\n")
    return str(p)
