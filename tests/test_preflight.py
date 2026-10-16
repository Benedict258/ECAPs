import socket
import pytest
from bench import preflight
from bench.common import RealRig, gguf_path
from ecaps.model_manager import CATALOG


def rig_in(tmp_path, with_models=True, bad_magic=None, binary=True):
    r = RealRig(binary=str(tmp_path / "llama-server"), models_dir=str(tmp_path / "models"))
    (tmp_path / "models").mkdir()
    if binary: (tmp_path / "llama-server").write_bytes(b"x" * 10)
    if with_models:
        for t in CATALOG:
            gguf_path(t, "q4", str(tmp_path / "models")).write_bytes(b"GGUF" + b"\0" * 100)
    if bad_magic:
        gguf_path(bad_magic, "q4", str(tmp_path / "models")).write_bytes(b"NOPE" + b"\0" * 100)
    return r


def by(checks): return {c.name: c for c in checks}


def good(**kw):
    d = dict(free_disk_gb=50, ram_available_gb=7.5, ram_total_gb=8, swap_used_gb=0.0); d.update(kw); return d


def test_all_pass(tmp_path):
    # models_dir is joined to ROOT in gguf_path; absolute path overrides the join
    checks, ok = preflight.run_preflight(rig_in(tmp_path), **good(ram_available_gb=7.0 + 0.0 + 1.0, ram_total_gb=16))
    assert ok, preflight.render(checks, ok)
    assert "RESULT: PASS" in preflight.render(checks, ok)


def test_missing_everything_fails_and_lists(tmp_path):
    checks, ok = preflight.run_preflight(rig_in(tmp_path, with_models=False, binary=False), **good())
    assert not ok
    txt = preflight.render(checks, ok)
    assert sum(l.startswith("[FAIL]") for l in txt.splitlines()) == 1 + len(CATALOG) and "RESULT: FAIL" in txt


def test_bad_gguf_header_fails(tmp_path):
    checks, ok = preflight.run_preflight(rig_in(tmp_path, bad_magic=CATALOG[0]), **good())
    assert not ok and "not a valid GGUF" in by(checks)[f"model {CATALOG[0].name}"].detail


def test_low_disk_fails(tmp_path):
    _, ok = preflight.run_preflight(rig_in(tmp_path), **good(free_disk_gb=0.5))
    assert not ok


def test_low_ram_and_swap_warn_but_do_not_fail(tmp_path):
    checks, ok = preflight.run_preflight(rig_in(tmp_path), **good(ram_available_gb=3, ram_total_gb=6, swap_used_gb=2))
    c = by(checks)
    assert ok and c["available RAM for the 7 GB budget run"].status == "WARN" and c["swap in use"].status == "WARN"
    assert c["total RAM vs 7 GB budget"].status == "WARN"
    assert "Close browsers" in c["available RAM for the 7 GB budget run"].detail


def test_never_opens_network(tmp_path, monkeypatch):
    def boom(*a, **k): raise AssertionError("preflight touched the network")
    monkeypatch.setattr(socket.socket, "connect", boom)
    monkeypatch.setattr(socket, "getaddrinfo", boom)
    preflight.run_preflight(rig_in(tmp_path, with_models=False), **good())


def test_cli_exit_code_nonzero_when_failing(monkeypatch, capsys):
    monkeypatch.setattr(preflight, "run_preflight", lambda rig, tiers=None: ([preflight.Check("x", "FAIL", "y")], False))
    assert preflight.main([]) == 3 and "RESULT: FAIL" in capsys.readouterr().out


def test_partial_run_only_needs_selected_models(tmp_path):
    r = rig_in(tmp_path, with_models=False)
    gguf_path(CATALOG[0], "q4", str(tmp_path / "models")).write_bytes(b"GGUF" + b"\0" * 100)
    _, ok_small = preflight.run_preflight(r, tiers=[CATALOG[0]], **good(ram_total_gb=16))
    _, ok_all = preflight.run_preflight(r, **good(ram_total_gb=16))
    assert ok_small and not ok_all
