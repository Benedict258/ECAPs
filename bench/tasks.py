"""20 deterministic B3 tasks: sensor snapshot -> checkable correct action (inputs only, no results)."""
OK = {"soil_moisture": 55.0, "tank_level": 70.0, "temperature": 24.0}


def _t(**kw): return {**OK, **kw}


TASKS = (
    [(_t(soil_moisture=v), ("set_pump", "on")) for v in (10.0, 15.0, 22.0, 5.0, 28.0)]
    + [(_t(tank_level=v), ("log_alert", None)) for v in (2.0, 5.0, 8.0, 0.0)]
    + [(_t(temperature=v), ("log_alert", None)) for v in (41.0, 45.0, 52.0)]
    + [(_t(soil_moisture=sm, tank_level=tl, temperature=tp), ("noop", None))
       for sm, tl, tp in ((50, 80, 25), (60, 50, 30), (35, 20, 20), (45, 90, 38), (70, 15, 22),
                          (33, 11, 39), (80, 60, 15), (40, 40, 40))]
)
assert len(TASKS) == 20


def is_correct(action, expected) -> bool:
    if not action:
        return False
    tool, state = expected
    if action.get("tool") != tool:
        return False
    args = action.get("args") or {}
    if tool == "set_pump":
        return args.get("state") == state
    if tool == "log_alert":
        return bool(str(args.get("msg", "")).strip())
    return True
