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


def read(*parts): return (ROOT.joinpath(*parts)).read_text()


def test_readme_landing_page_statements():
    r = read("README.md")
    for needle in ("Research and development stage", "prototype", "stand-in reference machine", "not ECAPs silicon",
                   "No real benchmark results have been produced yet", "## Security status", "## What is verified / not verified",
                   "## What this is"):
        assert needle in r, needle
    # no performance, energy or speed-comparison claims on the landing page
    assert not re.search(r"faster than|energy saved|saves energy|watts? saved|tokens/s", r, re.I)
    assert not re.search(r"\bMinna\b", r)


def test_readme_links_resolve():
    r = read("README.md")
    targets = set(re.findall(r"\]\(([^)#]+)\)", r)) | set(re.findall(r"`(docs/[A-Za-z0-9_]+\.md)`", r))
    targets = {t for t in targets if not t.startswith("http")}
    assert targets, "README should link to docs and diagrams"
    for t in targets:
        assert (ROOT / t).exists(), f"README links to missing {t}"
    for needle in ("node_family", "software_stack", "edge_cloud_collaboration"):
        assert f"assets/diagrams/{needle}.png" in r


def test_security_status_is_consistent_across_docs():
    r, d = read("README.md"), read("docs", "DESIGN.md")
    for needle in ("no authentication", "TLS"):
        assert needle.lower() in r.lower() and needle.lower() in d.lower()


def test_unverified_items_agree_in_readme_and_summary_banner():
    r = read("README.md")
    from bench import summary
    import inspect
    src = inspect.getsource(summary)
    for readme_needle, summary_needle in (("fake port", "fake port"), ("fake broker", "fake broker"), ("localhost", "localhost only"),
                                          ("17 Oct 2026", "17 Oct 2026")):
        assert readme_needle in r and summary_needle in src


def test_run_guide_marks_release_names_unverified_and_licences_recorded():
    g = read("docs", "RUN_ON_PC.md")
    assert "unverified" in g and "release page" in g
    assert "MIT" in read("docs", "MODELS.md")


def test_solar_doc_wording():
    d = read("docs", "NODE_SPEC_PROPOSED.md")
    for needle in ("Abuja-area estimate, old data", "4.85", "5.11", "NIMET 1971-1980", "aijcrnet.com", "stated assumption", "no figure for the deployment site"):
        assert needle in d, needle
    assert "Minna" not in d


def test_dummy_output_is_gitignored():
    assert "results_dummy/" in read(".gitignore").splitlines()
