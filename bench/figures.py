"""Poster figures, generated ONLY from results JSON. PNG @300dpi + SVG. Titles are computed from the data."""
from __future__ import annotations

import json
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from bench.common import ROOT, load_result, out_dir
from ecaps.environment import footer_line

BLUE, ORANGE, VERM, GREEN, GREY = "#0072B2", "#E69F00", "#D55E00", "#009E73", "#555555"   # Okabe-Ito
plt.rcParams.update({"font.size": 16, "axes.titlesize": 20, "axes.labelsize": 16, "svg.fonttype": "none",
                     "axes.spines.top": False, "axes.spines.right": False})


def _env(mock):
    p = out_dir(mock) / "environment.json"
    return json.loads(p.read_text())


def _finish(fig, name, mock, env, models, extra="", dummy=False):
    foot = ("DUMMY RUN in a cloud container, NOT the owner's PC. " if dummy else "") + footer_line(env, models) + (" | " + extra if extra else "")
    fig.text(0.02, 0.01, "\n".join(textwrap.wrap(foot, 150)), fontsize=11, color=GREY, va="bottom")
    if dummy:
        fig.text(0.5, 0.5, "DUMMY DATA\n(mock backend)", fontsize=70, color="red", alpha=0.18,
                 ha="center", va="center", rotation=25)
    fig.subplots_adjust(left=0.1, right=0.97, top=0.86, bottom=0.2)
    d = out_dir(mock) / "figures"
    d.mkdir(exist_ok=True)
    fig.savefig(d / f"{name}.png", dpi=300)
    fig.savefig(d / f"{name}.svg")
    plt.close(fig)


def f1(mock):
    r = load_result("b1_overhead", mock)
    if not r: return
    fig, ax = plt.subplots(figsize=(12, 7.5))
    for i, (k, c, lab) in enumerate((("direct", BLUE, "Raw llama-server"), ("runtime", ORANGE, "Via ECAPs runtime"))):
        m, s = r[k]["tps"]["mean"], r[k]["tps"]["std"]
        ax.bar(i, m, 0.55, yerr=s, color=c, capsize=8)
        ax.text(i, m + s, f"{m:.2f} ± {s:.2f}", ha="center", va="bottom", fontweight="bold")
        ax.text(i, m / 2, lab, ha="center", color="white", fontweight="bold")
    ax.set_xticks([]); ax.set_ylabel("Generation speed (tokens/s)")
    o = r["tps_overhead_pct"]
    ax.set_title(f"Runtime overhead vs raw llama-server: {o['mean']:.1f}% ± {o['std']:.1f}% (n={r['repeats']})")
    _finish(fig, "F1_overhead", mock, _env(mock), [r["model"]], f"threads={r['threads']}", r["dummy"])


def f2(mock):
    r = load_result("b2_autofit", mock)
    if not r: return
    fig, ax = plt.subplots(figsize=(12, 7.5))
    w, n_ok = 0.36, 0
    for i, row in enumerate(r["rows"]):
        for j, (key, c) in enumerate((("autofit", GREEN), ("naive_largest", VERM))):
            m = row[key]
            if not m: continue
            x = i + (j - 0.5) * w
            ax.bar(x, m["peak_rss_gb"]["mean"], w, yerr=m["peak_rss_gb"]["std"], color=c, capsize=6)
            ax.text(x, m["peak_rss_gb"]["mean"] + m["peak_rss_gb"]["std"] + 0.1,
                    m["model"].split("-instruct")[0], ha="center", fontsize=12, rotation=0)
        ax.hlines(row["budget_gb"], i - 0.45, i + 0.45, colors="black", linestyles="--", linewidth=2)
        ax.text(i + 0.45, row["budget_gb"], f" budget\n {row['budget_gb']} GB", va="center", fontsize=13)
        n_ok += bool(row["autofit"] and row["autofit"]["under_budget"])
    ax.set_xticks(range(len(r["rows"])), [f"{x['budget_gb']} GB" for x in r["rows"]])
    ax.set_xlabel("Software memory budget"); ax.set_ylabel("Peak RSS (GB)")
    ax.plot([], [], color=GREEN, lw=8, label="Auto-fit pick"); ax.plot([], [], color=VERM, lw=8, label="Naive: always largest")
    ax.legend(frameon=False, loc="upper left")
    ax.set_title(f"Auto-fit stayed under budget in {n_ok} of {len(r['rows'])} budgets")
    ax.set_xlim(-0.6, len(r["rows"]) - 0.2)
    models = sorted({row[k]["model"] for row in r["rows"] for k in ("autofit", "naive_largest") if row[k]})
    _finish(fig, "F2_autofit", mock, _env(mock), models, "software memory budget (not a change to physical RAM)", r["dummy"])


def f3(mock):
    r = load_result("b3_offline", mock)
    if not r: return
    a, b = r["modes"]["network_allowed"], r["modes"]["network_blocked"]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 7.5))
    for ax, key, ylab in ((ax1, "correct", f"Tasks correct (of {a['tasks']})"), (ax2, "latency_s", "Latency per task (s)")):
        for i, (m, c, lab) in enumerate(((a, BLUE, "Network\nallowed"), (b, ORANGE, "Network\nblocked"))):
            s = m[key]
            ax.bar(i, s["mean"], 0.6, yerr=s["std"], color=c, capsize=8)
            ax.text(i, s["mean"] + s["std"], f"{s['mean']:.1f}" if key == "correct" else f"{s['mean']:.2f}",
                    ha="center", va="bottom", fontweight="bold")
        ax.set_xticks([0, 1], ["Network\nallowed", "Network\nblocked"]); ax.set_ylabel(ylab)
    ax1.set_ylim(0, a["tasks"] * 1.12)
    fig.suptitle(f"With outbound network blocked: {b['correct']['mean']:.1f}/{b['tasks']} correct "
                 f"vs {a['correct']['mean']:.1f}/{a['tasks']} allowed", fontsize=20, y=0.96)
    n_out = len(b["outbound_attempts"] or [])
    _finish(fig, "F3_offline", mock, _env(mock), [r["model"]], f"outbound attempts while blocked: {n_out}; repeats={r['repeats']}", r["dummy"])


def stack_diagram(mock):
    fig, ax = plt.subplots(figsize=(12, 8)); ax.set_xlim(0, 12); ax.set_ylim(0, 9); ax.axis("off")

    def box(x, y, w, h, t, c, dashed=False):
        ax.add_patch(plt.Rectangle((x, y), w, h, fill=True, fc=c, alpha=0.9 if not dashed else 0.25,
                                   ec="black", lw=2, ls="--" if dashed else "-"))
        ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=16, fontweight="bold",
                color="white" if not dashed else "black")
    box(1, 7, 6, 1.2, "Device interface\n(simulated feed; ESP32 planned)", BLUE)
    box(1, 5.2, 6, 1.2, "Agent runtime  sense → plan → act", GREEN)
    box(1, 3.4, 6, 1.2, "Model manager (memory auto-fit)", ORANGE)
    box(1, 1.6, 6, 1.2, "Backend: llama.cpp (CPU)", GREY)
    box(8, 5.2, 3.5, 1.2, "Memory (SQLite)", GREEN)
    box(8, 7, 3.5, 1.2, "Power manager\n(planned)", "#CCCCCC", True)
    box(8, 3.4, 3.5, 1.2, "Management API\n(planned)", "#CCCCCC", True)
    box(8, 1.6, 3.5, 1.2, "Node discovery\n(planned)", "#CCCCCC", True)
    for y0, y1 in ((7, 6.4), (5.2, 4.6), (3.4, 2.8)):
        ax.annotate("", xy=(4, y1), xytext=(4, y0), arrowprops=dict(arrowstyle="-|>", lw=3))
    ax.annotate("", xy=(8, 5.8), xytext=(7, 5.8), arrowprops=dict(arrowstyle="<->", lw=3))
    ax.set_title("ECAPs Node Runtime software stack (research prototype)", fontsize=20)
    ax.text(0.2, 0.3, "Dashed = planned, not implemented. Software only; no ECAPs silicon.", fontsize=14, color=GREY)
    d = out_dir(mock) / "figures"; d.mkdir(exist_ok=True)
    fig.savefig(d / "stack_diagram.svg"); fig.savefig(d / "stack_diagram.png", dpi=300); plt.close(fig)


def make_all(mock: bool):
    for f in (f1, f2, f3, stack_diagram):
        f(mock)
