import pytest
from ecaps import spec_calc as s


def test_weights_and_memory():
    assert s.weights_gb(7) == 3.5 and s.weights_gb(30) == 15.0 and s.weights_gb(7, 16) == 14.0 and s.weights_gb(7, 8) == 7.0
    assert s.memory_needed_gb(7) == pytest.approx(4.375)
    assert s.memory_needed_gb(7, os_headroom=True) == pytest.approx(5.375)


def test_ceilings_match_the_proposed_examples():
    assert s.tokens_per_s_ceiling(100, 7) == pytest.approx(28.57, abs=0.01)      # "about 28"
    assert s.tokens_per_s_ceiling(200, 30) == pytest.approx(13.33, abs=0.01)     # "about 13"


def test_solar_example():
    e = s.solar_example()
    assert e["daily_wh"] == 480 and e["battery_wh"] == 600
    assert e["panel_w"] == pytest.approx(137.14, abs=0.01)


def test_proposed_models_fit_proposed_memory():
    assert s.memory_needed_gb(3, os_headroom=True) <= 4      # Mini upper end
    assert s.memory_needed_gb(7, os_headroom=True) <= 8
    assert s.memory_needed_gb(30, os_headroom=True) <= 32


def test_table_renders():
    t = s.model_table()
    assert "Node Hub" in t and t.count("\n") == 4


def test_reported_sun_hours_sensitivity():
    assert s.SUN_HOURS_REPORTED["Abuja (old NIMET data)"] == 4.85 and s.SUN_HOURS_REPORTED["Jos (old NIMET data)"] == 5.11
    assert s.solar_example(sun_hours=4.85)["panel_w"] == pytest.approx(141.38, abs=0.01)
    assert s.solar_example(sun_hours=5.11)["panel_w"] == pytest.approx(134.19, abs=0.01)
