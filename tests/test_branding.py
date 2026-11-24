"""Tests for the brand-channel skill's scripts/branding.py, through main with a fake Chrome."""

import base64
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


def test_the_watermark_sits_on_the_background_with_clear_space_around_its_strokes(tmp_path, capsys):
    run(tmp_path, Chrome(), capsys)
    root = ET.fromstring(svgs(tmp_path)["watermark"])
    assert CONFIG["palette"]["background"] in root.get("style")
    x, y, w, h = (float(v) for v in root.get("viewBox").split())
    assert w == h and (x + w / 2, y + h / 2) == pytest.approx(branding.ICON_CENTRE)
    ink = branding.ICON_REACH + (branding.WATERMARK_WEIGHT - branding.ICON_WEIGHT) / 2  # wider caps reach further
    assert w / 2 - ink >= 8  # spec units of clear space between the strokes and the edge


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


# The slide backdrop (owner, fourth gate 3 of #38): a dim test lab scene, generated once with Gemini and cached.

KEY = "test-key-never-printed"
JPEG = b"\xff\xd8\xff\xe0" + b"\0" * 64


class Gemini:
    """Records each request and answers with one PNG image, or raises an API error."""

    def __init__(self, error=None):
        self.bodies, self.error = [], error

    def __call__(self, body, key):
        self.bodies.append((body, key))
        if self.error:
            raise branding.thumbnail.ApiError(self.error)
        data = base64.b64encode(png_of(1376, 768)).decode()
        return {"candidates": [{"content": {"parts": [{"inlineData": {"mimeType": "image/png", "data": data}}]}}]}


class Jpeg:
    def __init__(self):
        self.inputs = []

    def __call__(self, image):
        self.inputs.append(image)
        return JPEG


def backdrop(root, capsys, *flags, gemini=None, jpeg=None, config=CONFIG, chrome=None):
    workspace(root, config=config)
    code = branding.main(
        ["example", "--backdrop", *flags], root=root, shoot=chrome or Chrome(), post=gemini, to_jpeg=jpeg or Jpeg()
    )
    out, err = capsys.readouterr()
    return code, out, err


@pytest.fixture
def key(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", KEY)


def test_the_backdrop_names_its_cost_and_needs_yes_before_paying(tmp_path, capsys, key):
    gemini = Gemini()
    code, _, err = backdrop(tmp_path, capsys, gemini=gemini)
    assert code == 3
    assert "USD 0.07" in err and "--yes" in err
    assert gemini.bodies == [] and not (folder(tmp_path) / "backdrop.jpg").exists()


def test_the_backdrop_with_yes_writes_a_16_9_jpeg_and_its_prompt_record(tmp_path, capsys, key):
    gemini, jpeg, chrome = Gemini(), Jpeg(), Chrome()
    code, out, err = backdrop(tmp_path, capsys, "--yes", gemini=gemini, jpeg=jpeg, chrome=chrome)
    assert code == 0 and "USD 0.07" in err
    ((body, sent_key),) = gemini.bodies
    assert sent_key == KEY and KEY not in out + err
    assert body["generationConfig"]["imageConfig"]["aspectRatio"] == "16:9"
    assert body["contents"][0]["parts"][0]["text"] == branding.BACKDROP_PROMPT
    assert "monitors" in branding.BACKDROP_PROMPT and "no text" in branding.BACKDROP_PROMPT
    assert jpeg.inputs == [png_of(1376, 768)] and chrome.shots == []
    assert (folder(tmp_path) / "backdrop.jpg").read_bytes() == JPEG
    record = json.loads((folder(tmp_path) / "backdrop.json").read_text())
    assert record == {"model": branding.thumbnail.MODEL, "prompt": branding.BACKDROP_PROMPT, "file": "backdrop.jpg"}
    report = json.loads(out)["backdrop"]
    assert report["image"] == "generated" and report["cost_usd"] == 0.07 and report["jpg"] == "branding/backdrop.jpg"


def test_a_backdrop_for_the_same_prompt_is_reused_without_paying(tmp_path, capsys, key):
    backdrop(tmp_path, capsys, "--yes", gemini=Gemini())
    gemini = Gemini()
    code, out, _ = backdrop(tmp_path, capsys, gemini=gemini)
    assert code == 0 and gemini.bodies == []
    assert json.loads(out)["backdrop"] | {"bytes": 0} == {
        "jpg": "branding/backdrop.jpg",
        "prompt": branding.BACKDROP_PROMPT,
        "image": "cached",
        "cost_usd": 0,
        "bytes": 0,
    }


def test_the_channel_backdrop_prompt_is_asked_and_a_new_prompt_pays_again(tmp_path, capsys, key):
    backdrop(tmp_path, capsys, "--yes", gemini=Gemini())
    config = edited(CONFIG, "branding.backdrop_prompt", "A dim server room with code on screens, no text")
    gemini = Gemini()
    assert backdrop(tmp_path, capsys, gemini=gemini, config=config)[0] == 3
    assert backdrop(tmp_path, capsys, "--yes", gemini=gemini, config=config)[0] == 0
    assert [body["contents"][0]["parts"][0]["text"] for body, _ in gemini.bodies] == [
        "A dim server room with code on screens, no text"
    ]


def test_a_backdrop_without_the_key_is_an_error(tmp_path, capsys, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    code, _, err = backdrop(tmp_path, capsys, "--yes", gemini=Gemini())
    assert code == 1 and "GEMINI_API_KEY is not set" in err


def test_a_failed_gemini_call_writes_no_backdrop(tmp_path, capsys, key):
    code, _, err = backdrop(tmp_path, capsys, "--yes", gemini=Gemini(error="HTTP 429: quota"))
    assert code == 1 and "Gemini: HTTP 429: quota" in err
    assert not (folder(tmp_path) / "backdrop.jpg").exists()
