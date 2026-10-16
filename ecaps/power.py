"""Power-aware modes (eco / normal / boost), driven by a SIMULATED battery/solar level.

What a mode changes: thread count, max output tokens, context size and model tier.
Nothing here measures watts. B4 reports CPU-seconds per task, an energy PROXY only.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict

from .model_manager import CATALOG, ModelTier, choose

MODES = ("eco", "normal", "boost")
# max_tokens / ctx are fixed per mode; threads are derived from the detected core count.
MODE_LIMITS = {"eco": {"max_tokens": 32, "ctx": 1024},
               "normal": {"max_tokens": 64, "ctx": 2048},
               "boost": {"max_tokens": 128, "ctx": 4096}}


@dataclass(frozen=True)
class ModePlan:
    mode: str
    tier: str
    threads: int
    max_tokens: int
    ctx: int

    def as_dict(self): return asdict(self)


def threads_for(mode: str, physical_cores: int) -> int:
    n = max(int(physical_cores or 1), 1)
    return {"eco": max(1, n // 4), "normal": max(1, n // 2), "boost": n}[mode]


class PowerManager:
    """Battery thresholds (percent): < eco_below -> eco; >= boost_at -> boost; solar lowers the
    boost threshold to boost_at_solar. Simple thresholds, no hysteresis (see docs/DESIGN.md)."""

    def __init__(self, budget_gb: float, physical_cores: int, quant: str = "q4",
                 eco_below: float = 30, boost_at: float = 80, boost_at_solar: float = 60,
                 catalog: list[ModelTier] | None = None):
        self.budget_gb, self.cores, self.quant = budget_gb, physical_cores, quant
        self.eco_below, self.boost_at, self.boost_at_solar = eco_below, boost_at, boost_at_solar
        self.catalog = sorted(catalog or CATALOG, key=lambda t: t.params_b)

    def mode_for(self, battery_pct: float, solar: bool = False) -> str:
        if not 0 <= battery_pct <= 100:
            raise ValueError("battery_pct must be within 0..100")
        if battery_pct < self.eco_below:
            return "eco"
        if battery_pct >= (self.boost_at_solar if solar else self.boost_at):
            return "boost"
        return "normal"

    def tier_for(self, mode: str) -> str:
        """eco -> smallest tier; normal and boost -> largest tier that fits the memory budget."""
        if mode == "eco":
            return self.catalog[0].name
        pick = choose(self.budget_gb, self.quant, self.catalog)["chosen"]
        return pick["name"] if pick else self.catalog[0].name

    def plan(self, mode: str) -> ModePlan:
        lim = MODE_LIMITS[mode]
        return ModePlan(mode, self.tier_for(mode), threads_for(mode, self.cores), lim["max_tokens"], lim["ctx"])

    def plan_for(self, battery_pct: float, solar: bool = False) -> ModePlan:
        return self.plan(self.mode_for(battery_pct, solar))
