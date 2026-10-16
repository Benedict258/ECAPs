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
