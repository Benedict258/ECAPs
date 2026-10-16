"""Guards that the docs and the code catalogue say the same thing about licences."""
import re
from pathlib import Path
from ecaps.model_manager import CATALOG

ROOT = Path(__file__).resolve().parent.parent


def test_catalog_licences_match_models_md():
    md = (ROOT / "docs" / "MODELS.md").read_text()
    expected = {"qwen2.5-1.5b-instruct": ("Apache-2.0", "Qwen/Qwen2.5-1.5B-Instruct"),
                "phi-3.5-mini-instruct": ("MIT", "microsoft/Phi-3.5-mini-instruct"),
                "qwen2.5-7b-instruct": ("Apache-2.0", "Qwen/Qwen2.5-7B-Instruct")}
    assert {t.name for t in CATALOG} == set(expected)
    for t in CATALOG:
        lic, repo = expected[t.name]
        assert t.licence == lic
        assert f"https://huggingface.co/{repo}" in md
    assert "17 Oct 2026" in md and "MIT" in md and "ggml-org/llama.cpp" in md


def test_poster_slots_doc_matches_code():
    """The slot doc must name the real figure files and commands."""
    doc = (ROOT / "docs" / "POSTER_FIGURE_SLOTS.md").read_text()
    for needle in ("F1_overhead", "F2_autofit", "F3_offline", "F4_power_modes", "bench.run_all --only b1", "--only b2", "--only b3",
                   "--only b4", "bench.check_results", "bench.figures", "assets.make_diagrams", "DUMMY"):
        assert needle in doc, needle
    figs = (ROOT / "bench" / "figures.py").read_text()
    for name in ("F1_overhead", "F2_autofit", "F3_offline", "F4_power_modes"):
        assert f'"{name}"' in figs
    for extra in ("software memory budget (not a change to physical RAM)", "energy proxy only, no watts measured", "outbound attempts while blocked"):
        assert extra in figs and extra in doc
