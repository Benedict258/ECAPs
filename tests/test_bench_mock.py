import json
from bench import run_all
from bench.common import out_dir
from bench.tasks import TASKS


def test_tasks_count():
    assert len(TASKS) == 20


def test_mock_pipeline_end_to_end():
    assert run_all.main(["--mock", "--repeats", "5"]) == 0
    d = out_dir(True)
    for n in ("b1_overhead", "b2_autofit", "b3_offline"):
        j = json.loads((d / f"{n}.json").read_text())
        assert j["dummy"] is True
    b3 = json.loads((d / "b3_offline.json").read_text())
    assert b3["modes"]["network_blocked"]["outbound_attempts"] == []
    assert 0 < b3["modes"]["network_blocked"]["correct"]["mean"] < 20   # mock errs on purpose; failures kept
    for f in ("F1_overhead", "F2_autofit", "F3_offline", "stack_diagram"):
        assert (d / "figures" / f"{f}.png").exists() and (d / "figures" / f"{f}.svg").exists()
    assert "DUMMY" in (d / "summary.md").read_text()


def test_real_mode_refuses_without_models(capsys, monkeypatch):
    from bench.common import RealRig
    monkeypatch.setattr(RealRig, 'missing', lambda self, tiers: ['fake-missing-file'])
    assert run_all.main([]) == 3
    assert "Nothing was downloaded" in capsys.readouterr().err
