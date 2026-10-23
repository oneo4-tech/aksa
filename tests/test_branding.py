"""Tests for the brand-channel skill's scripts/branding.py, through main with a fake Chrome."""

import json
import struct
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from test_youtube_channel import CONFIG, edited, workspace

# A script serving one skill stays in the skill (components.md), outside the pytest pythonpath.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agentic/skills/content/brand-channel/scripts"))
import branding

SVG = "{http://www.w3.org/2000/svg}"
SIZES = {
    "avatar": (800, 800),
    "banner": (2048, 1152),
    "watermark": (150, 150),
    "wordmark-testlab": (2400, 320),
    "wordmark-aksa": (2400, 403),
}
OTHER = {"background": "#101820", "syntax": "#E60000", "name": "#FFFFFF", "suffix": "#3FFF8A"}


def png_of(width, height, extra=0):
    """PNG signature and IHDR of the given size, as much of a PNG as branding.py reads, padded by extra bytes."""
    header = struct.pack(">I", 13) + b"IHDR" + struct.pack(">II", width, height) + b"\x08\x06\x00\x00\x00"
    return b"\x89PNG\r\n\x1a\n" + header + b"\0" * (4 + extra)


class Chrome:
    """Records each shot and answers with a PNG of the asked size, or of a fixed size or padding."""

    def __init__(self, size=None, extra=0):
        self.size, self.extra, self.shots = size, extra, []

    def __call__(self, svg, size):
        self.shots.append((svg, size))
        return png_of(*(self.size or size), extra=self.extra)


def run(root, chrome, capsys, config=CONFIG):
    workspace(root, config=config)
    code = branding.main(["example"], root=root, shoot=chrome)
    out, err = capsys.readouterr()
    return code, out, err


def folder(root):
    return workspace(root, config=None, guide=False) / "branding"


def svgs(root):
    return {name: (folder(root) / f"{name}.svg").read_text() for name in SIZES}


def test_main_writes_each_asset_as_svg_and_png_at_its_youtube_size(tmp_path, capsys):
    chrome = Chrome()
    code, out, _ = run(tmp_path, chrome, capsys)
    assert code == 0
    report = {asset["name"]: asset for asset in json.loads(out)["assets"]}
    assert {name: (a["width"], a["height"]) for name, a in report.items()} == SIZES
    assert [size for _, size in chrome.shots] == list(SIZES.values())
    for name, (width, height) in SIZES.items():
        root = ET.fromstring((folder(tmp_path) / f"{name}.svg").read_text())
        assert (root.get("width"), root.get("height")) == (str(width), str(height))
        assert struct.unpack(">II", (folder(tmp_path) / f"{name}.png").read_bytes()[16:24]) == (width, height)
    assert report["avatar"]["limit"] == 15_000_000
    assert report["banner"]["limit"] == 6_000_000
    assert report["watermark"]["limit"] == 1_000_000


def test_banner_wordmark_and_lines_sit_inside_the_centred_safe_area(tmp_path, capsys):
    run(tmp_path, Chrome(), capsys)
    root = ET.fromstring(svgs(tmp_path)["banner"])
    left, top = (2048 - 1235) / 2, (1152 - 338) / 2
    right, bottom = left + 1235, top + 338
    (logo,) = root.findall(f"{SVG}svg")
    x, y, w, h = (float(logo.get(k)) for k in ("x", "y", "width", "height"))
    assert left <= x and x + w <= right and top <= y and y + h <= bottom
    assert x + w / 2 == pytest.approx(1024, abs=0.1)
    lines = root.findall(f"{SVG}text")
    assert [line.text for line in lines] == [CONFIG["branding"]["tagline"], CONFIG["branding"]["subline"]]
    for line in lines:
        size, baseline = float(line.get("font-size")), float(line.get("y"))
        assert (line.get("x"), line.get("text-anchor")) == ("1024", "middle")
        assert top <= baseline - 0.75 * size and baseline + 0.25 * size <= bottom
        assert len(line.text) * branding.CHAR_EM * size <= 1235


def test_the_banner_carries_the_first_wordmark(tmp_path, capsys):
    run(tmp_path, Chrome(), capsys)
    assert "translate(908,0)" in svgs(tmp_path)["banner"]  # testlab's seventh glyph, b, at 500 + 6 x 68; aksa has 4


def test_a_palette_change_changes_every_asset(tmp_path, capsys):
    run(tmp_path / "a", Chrome(), capsys)
    run(tmp_path / "b", Chrome(), capsys, config=edited(CONFIG, "palette", OTHER))
    before, after = svgs(tmp_path / "a"), svgs(tmp_path / "b")
    for name in SIZES:
        assert before[name] != after[name], name
        assert CONFIG["palette"]["syntax"] in before[name] and OTHER["syntax"] in after[name]
        assert CONFIG["palette"]["syntax"] not in after[name]


def strokes(svg):
    """The stroke colour of each stroked group, in document (drawing) order."""
    return [g.get("stroke") for g in ET.fromstring(svg).iter(f"{SVG}g") if g.get("stroke")]


@pytest.mark.parametrize("name", list(SIZES))
def test_syntax_strokes_are_drawn_last_over_the_name_strokes(tmp_path, capsys, name):
    run(tmp_path, Chrome(), capsys)
    palette = CONFIG["palette"]
    order = strokes(svgs(tmp_path)[name])
    assert order[-1] == palette["syntax"] and order.count(palette["syntax"]) == 1
    assert palette["name"] in order


def test_wordmarks_follow_the_spec_weights_and_suffix_advance(tmp_path, capsys):
    run(tmp_path, Chrome(), capsys)
    root = ET.fromstring(svgs(tmp_path)["wordmark-testlab"])
    weights = {g.get("stroke"): g.get("stroke-width") for g in root.iter(f"{SVG}g") if g.get("stroke")}
    palette = CONFIG["palette"]
    assert weights == {palette["name"]: "14", palette["suffix"]: "8.4", palette["syntax"]: "14"}
    assert root.get("viewBox") == "-10 16 990 132"  # the spec's testlab artboard
    shifts = [g.get("transform") for g in root.iter(f"{SVG}g") if g.get("transform")]
    assert [f"translate({500 + 68 * i},0)" for i in range(7)] == shifts[-9:-2]


def test_a_suffix_letter_without_a_glyph_is_refused_naming_it(tmp_path, capsys):
    config = edited(CONFIG, "branding.wordmarks", ["testlab", "pixel"])
    code, _, err = run(tmp_path, Chrome(), capsys, config=config)
    assert code == 2
    assert "pixel" in err and "'p'" in err and "'i'" in err and "'x'" in err
    assert not folder(tmp_path).exists()


def test_a_banner_line_too_wide_for_the_safe_area_is_refused(tmp_path, capsys):
    config = edited(CONFIG, "branding.tagline", "How testers think when AI writes all of the code")
    code, _, err = run(tmp_path, Chrome(), capsys, config=config)
    assert code == 2 and "branding.tagline" in err
    assert not folder(tmp_path).exists()


def test_a_render_over_its_youtube_limit_is_an_error(tmp_path, capsys):
    code, _, err = run(tmp_path, Chrome(extra=1_000_000), capsys)
    assert code == 1 and "watermark" in err and "1000000" in err


def test_a_render_at_the_wrong_size_is_an_error(tmp_path, capsys):
    code, _, err = run(tmp_path, Chrome(size=(10, 10)), capsys)
    assert code == 1 and "10x10" in err and "800x800" in err


def test_an_invalid_channel_is_refused(tmp_path, capsys):
    code, _, err = run(tmp_path, Chrome(), capsys, config=edited(CONFIG, "branding"))
    assert code == 2 and "branding: missing" in err
