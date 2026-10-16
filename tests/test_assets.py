"""The poster asset kit must be reproducible from the script, carry no results/spec numbers, and be 300 dpi."""
import re
import struct
from pathlib import Path
import pytest
from assets import make_diagrams

NAMES = ("node_family", "software_stack", "edge_cloud_collaboration")
ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def out(tmp_path_factory):
    d = tmp_path_factory.mktemp("diagrams")
    make_diagrams.make_all(d)
    return d


def png_dpi(path):
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    i = 8
    while i < len(data):
        n, kind = struct.unpack(">I4s", data[i:i + 8])
        if kind == b"pHYs":
            x, y, unit = struct.unpack(">IIB", data[i + 8:i + 17])
            assert unit == 1
            return round(x * 0.0254), round(y * 0.0254)
        i += 12 + n
    raise AssertionError("no pHYs chunk")


def test_files_written_svg_and_png_300dpi(out):
    for n in NAMES:
        assert (out / f"{n}.svg").exists()
        assert png_dpi(out / f"{n}.png") == (300, 300)


def test_svg_text_stays_text_and_has_no_spec_or_result_numbers(out):
    for n in NAMES:
        svg = (out / f"{n}.svg").read_text()
        texts = " ".join(re.findall(r">([^<>]+)</text>", svg))
        assert texts, "SVG text should stay selectable text"
        # no spec/result units anywhere in the labels
        assert not re.search(r"\d\s*(GB|W|Wh|kWh|GB/s|tokens|tok/s|%|ms|s)\b", texts), texts
        assert not re.search(r"\bDUMMY\b", texts)
    assert "PROPOSED" in (out / "node_family.svg").read_text()


def test_labels_required_by_the_brief(out):
    fam = (out / "node_family.svg").read_text()
    for needle in ("Node Mini", "Node Hub", "Tier 1", "Tier 2", "Cloud partner", "optional, when online", "one software stack"):
        assert needle in fam
    stack = (out / "software_stack.svg").read_text()
    for needle in ("Device interface", "Agent runtime", "Model manager", "llama.cpp", "Power manager", "Memory", "Management API",
                   "Node discovery", "Outbox", "localhost only", "mock"):
        assert needle in stack
    ec = (out / "edge_cloud_collaboration.svg").read_text()
    for needle in ("Local-first answer", "Escalate when needed", "Queue when offline", "Update when online"):
        assert needle in ec


def test_committed_kit_exists():
    for n in NAMES:
        assert (ROOT / "assets" / "diagrams" / f"{n}.svg").exists() and (ROOT / "assets" / "diagrams" / f"{n}.png").exists()
