import pytest
from ecaps.model_manager import choose, main


@pytest.mark.parametrize("budget,name", [(2, "qwen2.5-1.5b-instruct"), (4, "phi-3.5-mini-instruct"),
                                         (7, "qwen2.5-7b-instruct")])
def test_tier_per_budget(budget, name):
    r = choose(budget)
    assert r["chosen"]["name"] == name
    assert r["estimated_required_gb"] <= budget and r["reason"]


def test_nothing_fits():
    r = choose(1)
    assert r["chosen"] is None and "No tier fits" in r["reason"]


def test_q8_picks_smaller_when_tight():
    assert choose(4, "q8")["chosen"]["name"] == "qwen2.5-1.5b-instruct"


def test_cli(capsys):
    main(["--budget-gb", "7"])
    assert "qwen2.5-7b" in capsys.readouterr().out
