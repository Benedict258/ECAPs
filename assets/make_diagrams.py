"""Poster asset kit: three concept diagrams, NO results and NO spec figures.
    python -m assets.make_diagrams [--out assets/diagrams]
Writes SVG and PNG (300 dpi). Large fonts, Okabe-Ito colour-blind-safe palette; meaning is always carried by text as well as colour.
Everything shown here is a PROPOSED design or a statement already in README.md / docs/DESIGN.md; no numbers are plotted."""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

BLUE, ORANGE, GREEN, VERM, SKY, GREY, INK = "#0072B2", "#E69F00", "#009E73", "#D55E00", "#56B4E9", "#555555", "#111111"
plt.rcParams.update({"svg.fonttype": "none", "font.family": "DejaVu Sans"})


def canvas(w=16, h=9):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, w); ax.set_ylim(0, h); ax.axis("off")
    fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
    return fig, ax


def box(ax, x, y, w, h, fc, ec=INK, dashed=False, alpha=1.0, lw=3, round_=0.15):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={round_}", fc=fc, ec=ec, lw=lw,
                                ls="--" if dashed else "-", alpha=alpha))


def text(ax, x, y, s, size=18, color=INK, weight="normal", ha="center", va="center", **kw):
    ax.text(x, y, s, fontsize=size, color=color, fontweight=weight, ha=ha, va=va, linespacing=1.3, **kw)


def pill(ax, x, y, s, fc=ORANGE, color=INK, size=16, w=2.0, h=0.5):
    box(ax, x - w / 2, y - h / 2, w, h, fc, lw=2, round_=0.25)
    text(ax, x, y, s, size, color, "bold")


def arrow(ax, p, q, dashed=False, both=False, lw=3.5, color=INK):
    ax.annotate("", xy=q, xytext=p, arrowprops=dict(arrowstyle="<|-|>" if both else "-|>", lw=lw, color=color,
                                                     ls="--" if dashed else "-", shrinkA=0, shrinkB=0, mutation_scale=28))


def save(fig, name: str, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / f"{name}.svg")
    fig.savefig(out / f"{name}.png", dpi=300)
    plt.close(fig)


# --------------------------------------------------------------------------- 1. node family
def node_family(out: Path):
    fig, ax = canvas()
    text(ax, 8, 8.65, "ECAPs node family: one architecture, three sizes", 29, weight="bold")
    pill(ax, 14.0, 7.55, "ALL PROPOSED", ORANGE, size=17, w=2.9, h=0.6)

    box(ax, 4.6, 6.65, 6.8, 1.45, "white", dashed=True)
    text(ax, 8, 7.55, "Cloud partner", 24, weight="bold")
    text(ax, 8, 7.02, "optional, when online", 18, GREY)

    y0 = 1.6
    specs = [(0.6, 3.5, SKY, INK, "Node Mini", ["Plug-in compute add-on", "for a host board", "For robotics and", "engineering systems"]),
             (5.8, 3.9, GREEN, "white", "Node", ["Home or institution", "Tier 1"]),
             (11.0, 4.3, BLUE, "white", "Node Hub", ["Shared community node", "Tier 2", "Networkable, like a rack"])]
    for x, h, fc, tc, title, lines in specs:
        w = 4.4
        box(ax, x, y0, w, h, fc)
        text(ax, x + w / 2, y0 + h - 0.5, title, 26, tc, "bold")
        for i, ln in enumerate(lines):
            text(ax, x + w / 2, y0 + h - 1.15 - 0.47 * i, ln, 18, tc)
        pill(ax, x + w / 2, y0 + 0.42, "PROPOSED", ORANGE, INK, 15, 1.9, 0.5)
        arrow(ax, (x + w / 2, y0 + h + 0.05), (8 + (x + w / 2 - 8) * 0.3, 6.6), dashed=True, both=True, lw=3, color=GREY)
    text(ax, 2.6, 6.3, "dashed: optional,\nonly when online", 16, GREY)

    box(ax, 0.6, 0.5, 14.8, 0.85, "#E8E8E8", lw=2)
    text(ax, 8.0, 0.93, "One architecture  \u00b7  one software stack  \u00b7  three sizes", 21, weight="bold")
    text(ax, 8, 0.1, "Research and development stage. Names, sizes and roles are proposals; no ECAPs hardware exists.", 15, GREY, va="bottom")
    save(fig, "node_family", out)


# --------------------------------------------------------------------------- 2. software stack
def software_stack(out: Path):
    fig, ax = canvas()
    text(ax, 8, 8.7, "ECAPs Node Runtime: software stack and what is verified", 28, weight="bold")
    MOCK, PROTO, WRAP = SKY, ORANGE, "#CFCFCF"
    left = [("Device interface", ["simulated feed (default); serial and MQTT adapters", "TESTED: mock; serial/MQTT on fake port/broker only"], MOCK),
            ("Agent runtime  (sense > plan > act)", ["BUILT; TESTED: mock backend only"], MOCK),
            ("Model manager  (memory auto-fit)", ["BUILT; TESTED: unit tests; no real model run"], MOCK),
            ("Backend: llama.cpp wrapper", ["BUILT; NEVER RUN against a real server yet"], WRAP)]
    ys = [6.6, 4.85, 3.1, 1.35]
    for (title, lines, fc), y in zip(left, ys):
        box(ax, 0.5, y, 7.4, 1.4, fc)
        text(ax, 4.2, y + 1.02, title, 21, weight="bold")
        for i, ln in enumerate(lines):
            text(ax, 4.2, y + 0.62 - 0.33 * i, ln, 14)
    for a, b in zip(ys[:-1], ys[1:]):
        arrow(ax, (4.2, a - 0.02), (4.2, b + 1.42))
    right = [("Power manager", "BUILT; TESTED: mock only", MOCK),
             ("Memory  (SQLite)", "BUILT; TESTED: mock only", MOCK),
             ("Outbox / queue", "BUILT; cloud sync: localhost test only", MOCK),
             ("Management API", "BUILT; functional tests only", MOCK),
             ("Node discovery + routing", "PROTOTYPE; localhost only", PROTO)]
    ry = [7.0, 5.75, 4.5, 3.25, 2.0]
    for (title, status, fc), y in zip(right, ry):
        box(ax, 8.9, y, 6.6, 1.0, fc)
        text(ax, 12.2, y + 0.66, title, 19, weight="bold")
        text(ax, 12.2, y + 0.28, status, 14)
    # legend (text carries the meaning; colour is secondary)
    for i, (fc, s) in enumerate([(MOCK, "built, tested on mock / fake devices only"), (PROTO, "prototype, tested on localhost only"),
                                 (WRAP, "built, real server not yet run")]):
        x = 0.5 + i * 5.2
        box(ax, x, 0.35, 0.5, 0.4, fc, lw=2, round_=0.08)
        text(ax, x + 0.65, 0.55, s, 14, ha="left")
    save(fig, "software_stack", out)


# --------------------------------------------------------------------------- 3. edge-cloud collaboration
def edge_cloud(out: Path):
    fig, ax = canvas()
    text(ax, 8, 8.7, "Edge-cloud collaboration: local first, cloud as a partner", 28, weight="bold")
    box(ax, 5.2, 6.7, 5.6, 1.4, "white", dashed=True)
    text(ax, 8, 7.58, "Cloud partner", 24, weight="bold")
    text(ax, 8, 7.05, "optional, when online", 18, GREY)

    box(ax, 0.5, 0.95, 15.0, 4.55, "#F2F2F2", lw=2.5, round_=0.25)
    text(ax, 1.0, 1.35, "Local node: keeps working with no network", 20, weight="bold", ha="left")
    box(ax, 0.9, 1.95, 3.1, 2.55, "white")
    text(ax, 2.45, 3.22, "Sensors\nand users", 22, weight="bold")
    box(ax, 4.6, 1.95, 4.7, 2.55, GREEN)
    text(ax, 6.95, 3.85, "1  Local-first answer", 22, "white", "bold")
    text(ax, 6.95, 2.9, "The node senses, decides\nand acts on its own", 18, "white")
    box(ax, 10.6, 1.95, 4.5, 2.55, SKY)
    text(ax, 12.85, 3.85, "3  Queue when offline", 22, INK, "bold")
    text(ax, 12.85, 2.9, "Events and actions wait\nin a local queue", 18)
    arrow(ax, (4.05, 3.22), (4.55, 3.22))
    arrow(ax, (9.35, 3.22), (10.55, 3.22))
    text(ax, 9.95, 3.62, "no link", 16, GREY)

    arrow(ax, (6.4, 4.55), (6.7, 6.65), dashed=True, lw=3.5)
    box(ax, 1.5, 5.75, 4.85, 0.85, "white", lw=2)
    text(ax, 3.92, 6.18, "2  Escalate when needed", 19, weight="bold")
    arrow(ax, (11.4, 4.55), (10.1, 6.65), dashed=True, both=True, lw=3.5)
    box(ax, 11.0, 5.75, 4.4, 0.85, "white", lw=2)
    text(ax, 13.2, 6.18, "4  Update when online", 19, weight="bold")

    text(ax, 8, 0.62, "Dashed arrows: only when configured and a link exists. Design intent: cloud escalation is a stub, off by default;", 15, GREY)
    text(ax, 8, 0.27, "queue sync has only been tested against a localhost server. Prototype, research and development stage.", 15, GREY)
    save(fig, "edge_cloud_collaboration", out)


def make_all(out: Path):
    for fn in (node_family, software_stack, edge_cloud):
        fn(out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent / "diagrams"))
    make_all(Path(ap.parse_args().out))
    print("wrote diagrams")
