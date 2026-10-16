import json
from bench import check_results
from ecaps.environment import commit_hash


def make(tmp_path, dummy=False, env_warning=False, commit=None, figs=True, summary="# ok\n"):
    r = tmp_path / "results"; (r / "figures").mkdir(parents=True)
    env = {"cpu_model": "Test CPU", "runtime_commit": commit or commit_hash()}
    if env_warning: env["warning"] = "DUMMY: cloud"
    (r / "environment.json").write_text(json.dumps(env))
    (r / "b1_overhead.json").write_text(json.dumps({"dummy": dummy}))
    if figs:
        for e in ("png", "svg"): (r / "figures" / f"F1_overhead.{e}").write_bytes(b"x")
    (r / "summary.md").write_text(summary)
    return r


def status(rows): return {n: s for s, n, _ in rows}


def test_good_results_pass_with_warnings_for_missing_slots(tmp_path):
    rows = check_results.check(make(tmp_path))
    st = status(rows)
    assert "FAIL" not in st.values() and st["b2_autofit"] == "WARN" and st["F1_overhead"] == "PASS"
    assert check_results.main([str(tmp_path / "results")]) == 0


def test_dummy_everywhere_fails(tmp_path):
    rows = check_results.check(make(tmp_path, dummy=True, env_warning=True, summary="> DUMMY DATA\n"))
    st = status(rows)
    assert st["b1_overhead"] == "FAIL" and st["environment.json"] == "FAIL" and st["summary.md"] == "FAIL"
    assert check_results.main([str(tmp_path / "results")]) == 1


def test_missing_figures_and_stale_commit(tmp_path):
    rows = check_results.check(make(tmp_path, figs=False, commit="deadbee"))
    st = status(rows)
    assert st["F1_overhead"] == "FAIL" and st["commit hash"] == "WARN"


def test_missing_results_dir_fails(tmp_path):
    assert check_results.main([str(tmp_path / "nope")]) == 1
