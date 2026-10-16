"""Arithmetic behind docs/NODE_SPEC_PROPOSED.md. These are FORMULAS applied to PROPOSED figures, not measurements.
Run `python -m ecaps.spec_calc` to print the tables used in that document."""
from __future__ import annotations

BYTES_PER_WEIGHT = {16: 2.0, 8: 1.0, 4: 0.5}
OVERHEAD = 1.25
OS_HEADROOM_GB = 1.0


def weights_gb(params_b: float, bits: int = 4) -> float:
    return params_b * BYTES_PER_WEIGHT[bits]


def memory_needed_gb(params_b: float, bits: int = 4, os_headroom: bool = False) -> float:
    return weights_gb(params_b, bits) * OVERHEAD + (OS_HEADROOM_GB if os_headroom else 0.0)


def tokens_per_s_ceiling(bandwidth_gb_s: float, params_b: float, bits: int = 4) -> float:
    """Upper bound for dense-model, batch-1 decoding: every weight is read once per token."""
    return bandwidth_gb_s / weights_gb(params_b, bits)


def daily_energy_wh(watts: float, hours: float = 24.0) -> float:
    return watts * hours


def battery_wh(daily_wh: float, usable_fraction: float = 0.8, days: float = 1.0) -> float:
    return daily_wh * days / usable_fraction


def panel_w(daily_wh: float, sun_hours: float = 5.0, efficiency: float = 0.7) -> float:
    return daily_wh / (sun_hours * efficiency)


# Sun-hour figures SUPPLIED by Benedict from an old dataset (NIMET 1971-1980, reported in a 2012 paper at aijcrnet.com, Vol 2 No 6).
# 1 kWh/m2/day is numerically 1 peak sun hour. Abuja-area estimate, OLD data. There is NO figure for the deployment site.
# The paper itself has not been read in this repo's build environment. The sizing default stays at the stated 5 h assumption.
SUN_HOURS_REPORTED = {"Abuja (old NIMET data)": 4.85, "Jos (old NIMET data)": 5.11}


# (name, params range in B, memory GB, bandwidth GB/s range, power W range)
PROPOSED = [
    ("Node Mini", (1, 3), "2-4", (25, 50), "3-5"),
    ("Node", (7, 7), "8", (100, 100), "10-25"),
    ("Node Hub", (13, 30), "32", (200, 200), "40-60"),
]


def model_table() -> str:
    rows = ["| Node | model size (4-bit) | weights GB | x1.25 GB | + 1 GB OS headroom GB | proposed memory GB | bandwidth GB/s | tokens/s ceiling |",
            "|---|---|---|---|---|---|---|---|"]
    for name, (p_lo, p_hi), mem, (bw_lo, bw_hi), _ in PROPOSED:
        def rng(f, lo, hi, nd=1):
            a, b = f(lo), f(hi)
            return f"{a:.{nd}f}" if abs(a - b) < 1e-9 else f"{min(a,b):.{nd}f} to {max(a,b):.{nd}f}"
        ps = f"{p_lo}B" if p_lo == p_hi else f"{p_lo}B to {p_hi}B"
        w = rng(lambda p: weights_gb(p), p_lo, p_hi)
        m = rng(lambda p: memory_needed_gb(p), p_lo, p_hi, 2)
        mo = rng(lambda p: memory_needed_gb(p, os_headroom=True), p_lo, p_hi, 2)
        bw = f"{bw_lo}" if bw_lo == bw_hi else f"{bw_lo} to {bw_hi}"
        # ceiling range: best = low params at high bandwidth, worst = high params at low bandwidth
        best = tokens_per_s_ceiling(bw_hi, p_lo)
        worst = tokens_per_s_ceiling(bw_lo, p_hi)
        tps = f"{best:.1f}" if abs(best - worst) < 1e-9 else f"{worst:.1f} to {best:.1f}"
        rows.append(f"| {name} | {ps} | {w} | {m} | {mo} | {mem} | {bw} | {tps} |")
    return "\n".join(rows)


def solar_example(watts: float = 20.0, sun_hours: float = 5.0, efficiency: float = 0.7, usable: float = 0.8) -> dict:
    d = daily_energy_wh(watts)
    return {"watts": watts, "daily_wh": d, "battery_wh": battery_wh(d, usable), "panel_w": panel_w(d, sun_hours, efficiency),
            "sun_hours": sun_hours, "efficiency": efficiency, "usable_fraction": usable}


if __name__ == "__main__":
    print(model_table())
    print()
    s = solar_example()
    print(f"daily energy = {s['watts']:.0f} W x 24 h = {s['daily_wh']:.0f} Wh/day")
    print(f"battery = {s['daily_wh']:.0f} / {s['usable_fraction']} = {s['battery_wh']:.0f} Wh")
    print(f"panel = {s['daily_wh']:.0f} / ({s['sun_hours']:.0f} x {s['efficiency']}) = {s['panel_w']:.1f} W")
    print("same sizing with the reported sun-hour figures (Abuja-area estimate, old data):")
    for place, h in SUN_HOURS_REPORTED.items():
        e = solar_example(sun_hours=h)
        print(f"  {place}: {h} h -> panel = {e['daily_wh']:.0f} / ({h} x {e['efficiency']}) = {e['panel_w']:.1f} W")
