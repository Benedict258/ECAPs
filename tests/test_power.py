import pytest
from ecaps.backend import MockBackend
from ecaps.node import Node
from ecaps.power import PowerManager, MODE_LIMITS, threads_for


def pm(budget=4, cores=8): return PowerManager(budget, cores)


@pytest.mark.parametrize("b,solar,mode", [(0, False, "eco"), (29.9, False, "eco"), (30, False, "normal"),
                                          (79, False, "normal"), (80, False, "boost"), (100, False, "boost"),
                                          (60, True, "boost"), (59, True, "normal"), (10, True, "eco")])
def test_mode_thresholds(b, solar, mode):
    assert pm().mode_for(b, solar) == mode


def test_bad_level():
    with pytest.raises(ValueError): pm().mode_for(101)


def test_plans_scale_monotonically():
    p = pm(budget=7, cores=8)
    plans = [p.plan(m) for m in ("eco", "normal", "boost")]
    assert [x.threads for x in plans] == [2, 4, 8]
    assert [x.max_tokens for x in plans] == sorted(x.max_tokens for x in plans)
    assert [x.ctx for x in plans] == sorted(x.ctx for x in plans)
    assert plans[0].tier == "qwen2.5-1.5b-instruct" and plans[1].tier == plans[2].tier == "qwen2.5-7b-instruct"


def test_threads_never_zero():
    assert threads_for("eco", 1) == 1 and threads_for("eco", None) == 1


def test_node_switches_mode_and_restarts_backend():
    made, closed = [], []
    def factory(plan):
        made.append(plan.mode); return MockBackend(lambda p: '{"tool":"noop","args":{}}'), lambda: closed.append(plan.mode)
    n = Node(factory, pm(), battery_pct=90)
    assert n.plan.mode == "boost"
    n.step()
    n.set_power(10)
    assert n.plan.mode == "eco" and n.agent.max_tokens == MODE_LIMITS["eco"]["max_tokens"]
    n.set_power(12)                       # same mode: no restart
    assert made == ["boost", "eco"] and closed == ["boost"]
    assert n.metrics["mode_switches"] == 1 and n.metrics["steps"] == 1


def test_every_valid_action_fits_eco_token_cap():
    """Crude check: no real tokenizer here, so estimate tokens as ceil(chars/2) (pessimistic for JSON).
    Placeholder: must be re-checked with the real model's tokenizer."""
    import json, math
    from ecaps.devices import SimulatedSensors
    from ecaps.power import MODE_LIMITS
    from ecaps.tools import MAX_ALERT_CHARS, Toolbox
    tb = Toolbox(SimulatedSensors())
    cap = MODE_LIMITS["eco"]["max_tokens"]
    worst = {}
    for name, t in tb.tools.items():
        args = {}
        for k, spec in t.args.items():
            args[k] = max(spec, key=len) if isinstance(spec, list) else "x" * MAX_ALERT_CHARS
        worst[name] = {"tool": name, "args": args}
        tb.execute(worst[name])                      # it really is a valid action
    for name, action in worst.items():
        est = math.ceil(len(json.dumps(action, separators=(",", ":"))) / 2)
        assert est <= cap, f"{name}: ~{est} tokens > eco cap {cap}"


def test_overlong_alert_rejected():
    from ecaps.devices import SimulatedSensors
    from ecaps.tools import ActionError, Toolbox
    with pytest.raises(ActionError):
        Toolbox(SimulatedSensors()).execute({"tool": "log_alert", "args": {"msg": "x" * 61}})
