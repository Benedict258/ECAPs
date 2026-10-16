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
        L += ["> **DUMMY DATA from MockBackend, generated in a cloud container. NOT measurements. Do not use on the poster.**", ""]
    L += ["# ECAPs Node Runtime: results summary", "", "Research prototype. Stand-in reference machine, not ECAPs hardware.", "",
          f"**{footer_line(env)}**", ""]
    b1, b2, b3 = (load_result(n, mock) for n in ("b1_overhead", "b2_autofit", "b3_offline"))
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
    L += ["## Not run", "- B4 / F4 power modes: stretch item, not implemented, no data."]
    p = out_dir(mock) / "summary.md"
    p.write_text("\n".join(L) + "\n")
    return str(p)
