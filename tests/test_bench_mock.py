import json
from bench import run_all
from bench.common import out_dir
from bench.tasks import TASKS


def test_tasks_count():
    assert len(TASKS) == 20


def test_mock_pipeline_end_to_end():
    assert run_all.main(["--mock", "--repeats", "5"]) == 0
    d = out_dir(True)
    for n in ("b1_overhead", "b2_autofit", "b3_offline", "b4_power"):
        j = json.loads((d / f"{n}.json").read_text())
        assert j["dummy"] is True
    b3 = json.loads((d / "b3_offline.json").read_text())
    assert b3["modes"]["network_blocked"]["outbound_attempts"] == []
    assert 0 < b3["modes"]["network_blocked"]["correct"]["mean"] < 20   # mock errs on purpose; failures kept
    for f in ("F1_overhead", "F2_autofit", "F3_offline", "F4_power_modes", "stack_diagram"):
        assert (d / "figures" / f"{f}.png").exists() and (d / "figures" / f"{f}.svg").exists()
    assert "DUMMY" in (d / "summary.md").read_text()


def test_real_mode_refuses_without_models(capsys, monkeypatch):
    from bench.common import RealRig
    monkeypatch.setattr(RealRig, 'missing', lambda self, tiers: ['fake-missing-file'])
    assert run_all.main([]) == 3
    assert "Nothing was downloaded" in capsys.readouterr().err


def test_b4_mock_results_shape_and_proxy_label():
    d = out_dir(True)
    b4 = json.loads((d / "b4_power.json").read_text())
    assert set(b4["modes"]) == {"eco", "normal", "boost"} and b4["dummy"] is True
    for m in b4["modes"].values():
        assert m["cpu_seconds_per_task"]["n"] == 5 and m["cpu_seconds_per_task"]["mean"] >= 0
        assert m["tasks"] == 20
    assert "PROXY" in b4["note"]
    text = (d / "summary.md").read_text()
    assert "## B4 Power modes" in text and "no energy saving is claimed" in text
