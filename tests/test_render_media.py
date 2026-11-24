"""Media tests for the render-video skill's render.py and assemble.py: a two-scene fixture rendered twice with
the real whisper-cli, Chrome, and ffmpeg. Marked media; they run locally and are skipped in CI (#28)."""

import base64
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest
from test_assemble import assemble
from test_render import NUMBER, SCENES, WORDMARK, files, render
from test_youtube_channel import CONFIG

ISSUE = "https://github.com/oneo4-tech/aksa/issues/28"
pytestmark = [
    pytest.mark.media,
    pytest.mark.skipif(
        os.environ.get("CI") == "true", reason=f"CI has no Chrome, ffmpeg, whisper-cli, or fonts; run locally ({ISSUE})"
    ),
]
TERMINAL = {"kind": "terminal", "heading": "Run it", "visual": "$ pytest -q", "say": "S"}


@pytest.fixture(scope="module")
def tools():
    """Skip, naming what is missing, unless every tool, the whisper model, the fonts, and Chrome are here."""
    missing = [name for name in ["ffmpeg", "ffprobe", "whisper-cli"] if not shutil.which(name)]
    model = Path(os.environ.get(render.MODEL_VARIABLE) or render.WHISPER_MODEL)
    fonts = Path(os.environ.get(render.FONTS_VARIABLE) or render.FONTS_DIR)
    missing += [] if model.is_file() else [f"whisper model {model.name}"]
    missing += [f"font {name}" for name in render.FONTS.values() if not (fonts / name).is_file()]
    if missing:
        pytest.skip(f"missing {', '.join(missing)} (README, Setup)")
    from playwright.sync_api import Error, sync_playwright

    with sync_playwright() as playwright:
        try:
            playwright.chromium.launch(channel="chrome").close()
        except Error:
            pytest.skip("Google Chrome is not installed (README, Setup)")


def ffmpeg(*args):
    return subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True, capture_output=True, text=True).stdout


def probe(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-count_frames", "-of", "json", str(path)],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return json.loads(out)["streams"]


def frame_hashes(path):
    """One md5 per decoded frame."""
    lines = ffmpeg("-i", str(path), "-f", "framemd5", "-").splitlines()
    return [line.split(",")[-1].strip() for line in lines if not line.startswith("#")]


@pytest.mark.parametrize("kind, size", [("long-form", (1920, 1080)), ("short", (1080, 1920))])
def test_two_scenes_render_at_the_frame_size_with_identical_frames_on_two_renders(tmp_path, tools, kind, size):
    folder = files(tmp_path, scenes=[SCENES[1], TERMINAL], kind=kind, seconds=(1.5, 1.5), demo=True)
    # A 1920x1080 recording stands in for the VHS tape's demo.mp4; render only cuts and fits it.
    ffmpeg(
        "-f",
        "lavfi",
        "-i",
        "testsrc2=size=1920x1080:rate=30:duration=4",
        "-pix_fmt",
        "yuv420p",
        str(folder / "demo.mp4"),
    )
    renders = []
    for _ in range(2):
        assert render.main(["example", str(NUMBER)], root=tmp_path) == 0
        report = json.loads((folder / "render" / "scenes.json").read_text())
        renders.append([frame_hashes(folder / s["file"]) for s in report["scenes"]])
        for scene in report["scenes"]:
            streams = probe(folder / scene["file"])
            assert [s["codec_type"] for s in streams] == ["video"]  # silent: T13 adds the sound
            video = streams[0]
            assert (video["width"], video["height"], video["r_frame_rate"]) == (*size, "30/1")
            assert int(video["nb_read_frames"]) == scene["frames"]
    assert [s["source"] for s in report["scenes"]] == ["html", "demo"]
    assert renders[0] == renders[1]


def test_a_terminal_clip_longer_than_its_scene_is_sped_up_to_the_scenes_frames(tmp_path, tools):
    folder = files(tmp_path, scenes=[SCENES[0], TERMINAL], seconds=(1.5, 1.5), demo_json=False)
    # A 4 s clip for a 2.5 s scene plays 1.6 times faster.
    ffmpeg("-f", "lavfi", "-i", "testsrc2=size=1920x1080:rate=30:duration=4", "-pix_fmt", "yuv420p",
           str(folder / "demo-1.mp4"))  # fmt: skip
    assert render.main(["example", str(NUMBER)], root=tmp_path) == 0
    scene = json.loads((folder / "render" / "scenes.json").read_text())["scenes"][1]
    assert scene["source"] == "demo"
    assert int(probe(folder / scene["file"])[0]["nb_read_frames"]) == scene["frames"]


SAYS = ["The test mocks the discount. // So the assert only checks the fake.", "Run it... and it passes anyway."]


def loudness(path):
    """Integrated loudness (LUFS) and true peak (dBTP) of a file's audio, from ffmpeg's EBU R128 meter."""
    log = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", "ebur128=peak=true", "-f", "null", "-"],
        check=True,
        capture_output=True,
        text=True,
    ).stderr
    summary = log[log.rindex("Summary:") :]
    lufs, peak = re.search(r"I: +(-?[\d.]+) LUFS", summary), re.search(r"Peak: +(-?[\d.]+) dBFS", summary)
    return float(lufs[1]), float(peak[1])


@pytest.mark.parametrize("kind, size", [("long-form", (1920, 1080)), ("short", (1080, 1920))])
def test_two_scenes_assemble_with_captions_from_the_script_at_the_channels_loudness(tmp_path, tools, kind, size):
    if not shutil.which("say"):
        pytest.skip(f"macOS say is missing; it speaks the fixture's narration ({ISSUE})")
    scenes = [SCENES[1] | {"say": SAYS[0]}, TERMINAL | {"say": SAYS[1]}]
    folder = files(tmp_path, scenes=scenes, kind=kind, demo=True)
    for index, say in enumerate(SAYS, 1):  # real speech, so whisper times real words
        text = assemble.caption_words(say)
        wav = folder / "narration" / f"{index:02d}.wav"
        subprocess.run(["say", "-o", str(wav), "--data-format=LEI16@24000", " ".join(text)], check=True)
    ffmpeg(
        "-f",
        "lavfi",
        "-i",
        "testsrc2=size=1920x1080:rate=30:duration=8",
        "-pix_fmt",
        "yuv420p",
        str(folder / "demo.mp4"),
    )
    music = folder.parents[1] / "music"
    music.mkdir()
    ffmpeg("-f", "lavfi", "-i", "sine=frequency=220:duration=3", "-ac", "2", str(music / "bed.mp3"))  # loops
    finals = []
    for _ in range(2):
        assert render.main(["example", str(NUMBER)], root=tmp_path) == 0
        assert assemble.main(["example", str(NUMBER)], root=tmp_path) == 0
        final = folder / "render" / "final.mp4"
        finals.append(frame_hashes(final))
        streams = probe(final)
        video = next(s for s in streams if s["codec_type"] == "video")
        assert (video["width"], video["height"]) == size
        assert any(s["codec_type"] == "audio" for s in streams)
        lufs, peak = loudness(final)
        print(f"{kind}: {lufs} LUFS, true peak {peak} dBTP")
        assert abs(lufs - CONFIG["loudness"]["lufs"]) <= 1 and peak <= CONFIG["loudness"]["true_peak"]
    srt = folder / "render" / "final.srt"
    if kind == "long-form":
        texts = [" ".join(block.splitlines()[2:]) for block in srt.read_text().strip().split("\n\n")]
        assert " ".join(texts) == " ".join(w for say in SAYS for w in assemble.caption_words(say))
    else:
        assert not srt.exists()
    assert finals[0] == finals[1]


GEOMETRY = """() => {
  const box = e => { const r = e.getBoundingClientRect(); return {top: r.top, bottom: r.bottom, left: r.left, right: r.right}; };
  const rows = [...document.querySelectorAll('.line')];
  const arrows = [...document.querySelectorAll('.pointer path')];
  return {
    rows: rows.map(box),
    ends: rows.map(row => box(row.lastElementChild).right),
    glow: box(document.querySelector('.glow')),
    arrow: box(arrows[arrows.length - 1]),
    view: box(document.getElementById('code')),
    panel: box(document.getElementById('panel')),
  };
}"""


def code_geometry(lines, line, kind="long-form", seconds=4.0, scene=2, at=3):
    """Where the code scene puts its lines, focus band, and arrow once it has focused line, in page pixels."""
    from playwright.sync_api import sync_playwright

    size = render.SIZES[kind]
    cues = render.scene_cues(
        {"kind": "code", "heading": "H", "code": "demo/x.py"},
        scene,
        [],
        seconds - render.LEAD - render.TAIL,
        size,
        CONFIG,
        "\n".join(lines),
    )
    focus = [{"line": line, "at": 1.5}]
    cues["focus"] = [cue | {"top": top} for cue, top in zip(focus, render.scroll_tops(len(lines), focus, cues["rows"]))]
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome", args=render.CHROME_ARGS)
        try:
            tab = browser.new_page(viewport={"width": size[0], "height": size[1]})
            tab.set_content(render.page(cues, render.font_css(render.read_fonts())))
            assert tab.evaluate("window.ready") is True
            tab.evaluate(f"seek({at})")
            return tab.evaluate(GEOMETRY)
        finally:
            browser.close()


def centre(box):
    return (box["top"] + box["bottom"]) / 2


def test_code_focus_band_and_arrow_sit_on_the_focused_line_after_blank_lines(tools):
    # Content issue #38 scenes 3 and 11: blank lines rendered at another height, so band and arrow drifted.
    lines = ["import pytest", "", "def test_one():", "    assert one() == 1", "", "", "def test_two():", "    pass"]
    geometry = code_geometry(lines, 6)
    heights = [row["bottom"] - row["top"] for row in geometry["rows"]]
    assert max(heights) - min(heights) < 0.1, heights
    line, glow, arrow = geometry["rows"][6], geometry["glow"], geometry["arrow"]
    assert abs(glow["top"] - line["top"]) <= 1 and abs(glow["bottom"] - line["bottom"]) <= 1, (glow, line)
    assert abs(centre(arrow) - centre(line)) <= 1, (arrow, line)
    # The arrow points at the line's end, not at empty space at the panel's far side.
    char = heights[0] / 1.6 * 0.6
    assert 0 < arrow["left"] - geometry["ends"][6] <= 2 * char, (arrow, geometry["ends"][6])


@pytest.mark.parametrize("kind", ["long-form", "short"])
def test_a_focus_on_the_last_line_of_a_long_file_is_inside_the_visible_panel(tools, kind):
    lines = [f"value_{i} = {i}" for i in range(17)] + ["def last(): pass"]
    geometry = code_geometry(lines, 17, kind)
    line, view, panel = geometry["rows"][17], geometry["view"], geometry["panel"]
    for outer in (view, panel):
        assert outer["top"] <= line["top"] and line["bottom"] <= outer["bottom"], (line, outer)
    # Shown at the style guide's line count, scrolled, rather than shrunk to fit all 18.
    shown = [row for row in geometry["rows"] if view["top"] <= row["top"] and row["bottom"] <= view["bottom"]]
    assert len(shown) == render.ROWS[render.SIZES[kind]]
    assert abs(centre(geometry["arrow"]) - centre(line)) <= 1


@pytest.mark.parametrize("scene, whole", [(1, True), (2, False)])
def test_only_the_cold_opens_code_is_whole_on_the_first_frame(tools, scene, whole):
    lines = ["def apply_discount(price, percent):", "    return round(price * (1 - percent / 100), 2)"]
    geometry = code_geometry(lines, 0, scene=scene, at=0)
    widths = [row["right"] - row["left"] for row in geometry["rows"]]
    full = [end - row["left"] for end, row in zip(geometry["ends"], geometry["rows"])]
    if whole:
        assert all(w >= f - 1 for w, f in zip(widths, full)), (widths, full)
    else:
        assert widths == [0, 0], widths


def evaluate(cues, at, script, kind="long-form"):
    """script's result on the scene page built from cues, seeked to at seconds."""
    from playwright.sync_api import sync_playwright

    size = render.SIZES[kind]
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome", args=render.CHROME_ARGS)
        try:
            tab = browser.new_page(viewport={"width": size[0], "height": size[1]})
            tab.set_content(render.page(cues, render.font_css(render.read_fonts())))
            assert tab.evaluate("window.ready") is True
            tab.evaluate(f"seek({at})")
            return tab.evaluate(script)
        finally:
            browser.close()


AI_TESTS = [
    "from unittest.mock import patch",
    "",
    "from demo import discount",
    "",
    "",
    "def test_apply_discount():",
    '    with patch.object(discount, "apply_discount", return_value=90.0) as fake:',
    "        result = discount.apply_discount(100, 10)",
    "    assert result == 90.0",
    "    fake.assert_called_once()",
    "",
    "",
    "def test_apply_discount_runs():",
    "    result = discount.apply_discount(100, 10)",
    "    assert result is not None",
]
NOTES = """() => {
  const box = e => { const r = e.getBoundingClientRect(); return {top: r.top, bottom: r.bottom, left: r.left, right: r.right}; };
  const rows = [...document.querySelectorAll('.line')];
  return {
    rows: rows.map(box),
    ends: rows.map(row => box(row.lastElementChild).right),
    notes: [...document.querySelectorAll('.note')].map(n => ({...box(n), opacity: +getComputedStyle(n).opacity})),
    view: box(document.querySelector('.view')),
  };
}"""


@pytest.mark.parametrize("kind", ["long-form", "short"])
def test_mark_notes_sit_beside_their_line_without_covering_code_and_earlier_ones_dim(tools, kind):
    marks = [
        {"line": 7, "note": "patches the function under test", "at": "patch"},
        {"line": 15, "note": "any number passes", "at": "none"},
    ]
    cues = render.scene_cues(
        {"kind": "code", "heading": "H", "code": "tests/x.py", "marks": marks},
        2,
        [{"word": "patch", "start": 0.5, "end": 0.8}, {"word": "none", "start": 2.0, "end": 2.3}],
        4.0,
        render.SIZES[kind],
        CONFIG,
        "\n".join(AI_TESTS),
    )
    geometry = evaluate(cues, 4.0, NOTES, kind)
    view, rows, ends = geometry["view"], geometry["rows"], geometry["ends"]
    assert len(geometry["notes"]) == 2
    newest = geometry["notes"][-1]
    assert view["left"] <= newest["left"] and newest["right"] <= view["right"] + 1, (newest, view)
    assert view["top"] <= newest["top"] and newest["bottom"] <= view["bottom"] + 1, (newest, view)
    for note in geometry["notes"]:  # an earlier one may have scrolled away with its line
        # No code under the chip: every row it spans ends before it starts.
        for row, end in zip(rows, ends):
            if row["bottom"] > note["top"] + 2 and row["top"] < note["bottom"] - 2:
                assert end < note["left"], (row, end, note)
    # The newest mark is full; the earlier one stays, dimmed.
    assert geometry["notes"][0]["opacity"] < 0.6 and geometry["notes"][1]["opacity"] == 1


ENTRANCE = """() => {
  const text = document.querySelector('.point div'), style = getComputedStyle(text), r = text.getBoundingClientRect();
  const shift = style.transform === 'none' ? 0 : new DOMMatrix(style.transform).m41;
  return {opacity: +style.opacity, transform: style.transform, shift, width: text.offsetWidth};
}"""


def test_an_entrance_moves_mid_way_and_rests_in_place(tools):
    # Owner, #28: medium motion graphics; each element enters with a short eased move, then holds still.
    cues = render.staggered(
        render.scene_cues(
            {"kind": "points", "heading": "H", "visual": "Mocks replace code\nThe assert checks"},
            2,
            [{"word": "mocks", "start": 0.5, "end": 0.8}],
            3.0,
            render.SIZES["long-form"],
            CONFIG,
            None,
        )
    )
    start, enter = cues["items"][0]["at"] + 0.1, render.MOTION["enter"]
    before, middle, rest = (evaluate(cues, t, ENTRANCE) for t in (start - 0.05, start + enter / 8, start + enter + 0.1))
    assert before["opacity"] == 0
    assert 0 < middle["opacity"] < 1 and middle["transform"] != "none"
    assert rest["opacity"] == 1 and rest["transform"] in ("none", "matrix(1, 0, 0, 1, 0, 0)")
    # It slides in from the left to its place, a short move (at most MOTION offset of its width).
    assert -render.MOTION["offset"] * middle["width"] <= middle["shift"] < 0 and rest["shift"] == 0, (middle, rest)


INSIDE = """(selector) => [...document.querySelectorAll(selector)].map(e => {
  const r = e.getBoundingClientRect(), style = getComputedStyle(e);
  return {top: r.top, bottom: r.bottom, left: r.left, right: r.right, width: e.scrollWidth, box: e.clientWidth,
          opacity: +style.opacity, size: parseFloat(style.fontSize), text: e.textContent.slice(0, 30)};
})"""
CHECKOUT = "def order_total(cart, code, tax) -> int:\n    subtotal = sum(c * q for c, q in cart)\n    return subtotal\n"
NEW_KINDS = {
    "split": (
        {
            "kind": "split",
            "heading": "Spot the bug",
            "left": {"code": "demo/checkout.py", "label": "The code"},
            "right": {"code": "tests/test_checkout_ai.py", "label": "The AI's tests"},
        },
        {"left": CHECKOUT, "right": "\n".join(AI_TESTS)},
        ".side, .line",
    ),
    "compare": (
        {
            "kind": "compare",
            "heading": "Testing versus checking",
            "left": {"heading": "Checking", "items": ["Verifies a known proposition", "`assert total == 8991`"]},
            "right": {"heading": "Testing", "items": ["Learns by experimenting", "Flip a sign: `1 - p` to `1 + p`"]},
        },
        None,
        ".column h2, .item",
    ),
    "kit": (
        {
            "kind": "kit",
            "heading": "Take it to your agent",
            "repo": "oneo4-tech/testlab-demos",
            "path": "38-ai-test-mutation/ai-kit",
            "files": [
                {"path": "AGENTS.md", "use": "Paste into your AGENTS.md, CLAUDE.md, or Copilot instructions"},
                {
                    "path": "skills/check-test-can-fail/SKILL.md",
                    "use": "Copy into your skills folder; your agent runs it",
                },
                {
                    "path": "scripts/find_self_mocks.py",
                    "use": "Run on any test file to flag fakes of the code under test",
                },
                {
                    "path": "scripts/mutation_smoke.py",
                    "use": "Point at a source file and a test command; read what lived",
                },
            ],
            "takeaways": [
                "Mock collaborators, never the code under test",
                "Assert exact values, not types",
                "Break the code on purpose before you trust a test",
            ],
        },
        None,
        ".url, .takeaway",
    ),
    "intro": (
        {
            "kind": "intro",
            "heading": "Is this challenge for you?",
            "roles": ["Developers who let AI write their tests", "Testers who review AI-written code"],
            "activity": "Spot the bug in two AI-written unit tests",
            "stake": "They pass in CI, and would still pass if checkout overcharged",
        },
        None,
        ".role, .activity, .stake",
    ),
    "cta": (
        {"kind": "cta", "heading": "Help other testers find this", "actions": ["like", "share", "subscribe", "notify"]},
        None,
        ".action",
    ),
    "repo": (
        {
            "kind": "repo",
            "heading": "An AI kit for this problem",
            "repo": "oneo4-tech/testlab-demos",
            "path": "38-ai-test-mutation/ai-kit",
            "files": [
                "AGENTS.md",
                "skills/check-test-can-fail/SKILL.md",
                "scripts/find_self_mocks.py",
                "scripts/mutation_smoke.py",
            ],
        },
        None,
        ".head, .crumbs, .row, .url",
    ),
}


@pytest.mark.parametrize("kind", ["long-form", "short"])
@pytest.mark.parametrize("scene_kind", sorted(NEW_KINDS))
def test_new_kinds_show_every_element_whole_inside_the_frame_once_cued(tools, kind, scene_kind):
    scene, code, selector = NEW_KINDS[scene_kind]
    cues = render.staggered(render.scene_cues(scene, 2, [], 5.0, render.SIZES[kind], CONFIG, code))
    width, height = render.SIZES[kind]
    elements = evaluate(cues, cues["seconds"] - render.FADE - 0.05, f"() => ({INSIDE})('{selector}')", kind)
    assert elements
    for e in elements:
        assert 0 <= e["left"] and e["right"] <= width and 0 <= e["top"] and e["bottom"] <= height, e
        assert e["opacity"] == 1 and e["width"] <= e["box"] + 1, e  # shown, and no text cut off at its right
    if scene_kind == "kit":  # the link is large enough to read and type from
        assert elements[0]["size"] >= 26 and "https://github.com/" in elements[0]["text"], elements[0]
    if scene_kind == "repo":
        assert elements[-1]["size"] >= 26 and "https://github.com/" in elements[-1]["text"], elements[-1]


# Every drawn content element's box, clipped by its clipping ancestors (a scrolled code view hides its far lines);
# the grid, the title's veil, and bare svg canvases are backdrops, not content.
CONTENT = """() => [...document.querySelectorAll('#camera *')].flatMap(e => {
  if (e.matches('.grid, .veil, svg')) return [];
  let r = e.getBoundingClientRect(), top = r.top, bottom = r.bottom;
  for (let p = e.parentElement; p && p.id !== 'camera'; p = p.parentElement) {
    if (getComputedStyle(p).overflow === 'visible') continue;
    const c = p.getBoundingClientRect();
    top = Math.max(top, c.top);
    bottom = Math.min(bottom, c.bottom);
  }
  if (bottom - top < 1 || r.width < 1) return [];
  return [{tag: e.tagName, cls: String(e.className.baseVal ?? e.className), top, bottom,
           text: (e.textContent || '').slice(0, 30)}];
})"""
SHORT_KINDS = NEW_KINDS | {
    "title": ({"kind": "title", "heading": "Your turn", "visual": "Full breakdown: linked video"}, None, ""),
    "points": ({"kind": "points", "heading": "H", "visual": "Mocks replace code\nThe assert checks\nBreak it"}, None, ""),
    "terminal": ({"kind": "terminal", "heading": "Run it", "visual": "$ pytest -q\n1 passed\n$ mutmut run"}, None, ""),
    "code": ({"kind": "code", "heading": "It fakes the logic", "code": "tests/x.py",
              "marks": [{"line": 7, "note": "fakes the unit itself", "at": "patch"},
                        {"line": 15, "note": "any number passes", "at": "none"}]}, "\n".join(AI_TESTS), ""),
}  # fmt: skip


@pytest.mark.parametrize("scene_kind", sorted(SHORT_KINDS))
def test_short_scenes_draw_nothing_in_the_caption_band(tools, scene_kind):
    # Owner, #28 acceptance run (#39): the Short's burned captions covered the cold open's lower code panel.
    scene, code, _ = SHORT_KINDS[scene_kind]
    width, height = render.SIZES["short"]
    for index in (1, 2):  # the cold open and a later scene
        cues = render.staggered(render.scene_cues(scene, index, [], 3.0, (width, height), CONFIG, code))
        elements = evaluate(cues, cues["seconds"] - render.FADE - 0.05, CONTENT, "short")
        assert elements
        band = render.CAPTION_TOP * height
        assert all(e["bottom"] <= band for e in elements), [e for e in elements if e["bottom"] > band]


def test_short_captions_start_at_the_caption_band_top(tools):
    from playwright.sync_api import sync_playwright

    size = render.SIZES["short"]
    states = [{"words": ["The", "coupon", "logic"], "current": 1}]
    html = assemble.caption_page(states, size, CONFIG, render.font_css(render.read_fonts()))
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome", args=render.CHROME_ARGS)
        try:
            tab = browser.new_page(viewport={"width": size[0], "height": size[1]})
            tab.set_content(html)
            assert tab.evaluate("window.ready") is True
            tab.evaluate("show(0)")
            top = tab.evaluate("document.getElementById('line').getBoundingClientRect().top")
        finally:
            browser.close()
    assert abs(top - render.CAPTION_TOP * size[1]) <= 1, top


BACKDROP = """() => {
  const image = document.querySelector('.backdrop'), r = image.getBoundingClientRect();
  return {left: r.left, right: r.right, top: r.top, bottom: r.bottom, opacity: +getComputedStyle(image).opacity,
          first: document.getElementById('stage').firstElementChild === image, loaded: image.complete && image.naturalWidth > 0};
}"""


@pytest.mark.parametrize("kind", ["long-form", "short"])
def test_the_brand_image_sits_centred_faint_and_still_behind_a_code_scene(tools, kind):
    # Owner, #28 gate 3 (third review): the slides keep their colour, with the test lab image behind them.
    width, height = render.SIZES[kind]
    data = "data:image/svg+xml;base64," + base64.b64encode(WORDMARK.encode()).decode()
    scene = {"kind": "code", "heading": "H", "code": "tests/x.py"}
    cues = render.scene_cues(scene, 2, [], 4.0, (width, height), CONFIG, "\n".join(AI_TESTS))
    cues |= {"backdrop": {"image": data, "opacity": 0.1}}
    early, late = (evaluate(cues, t, BACKDROP, kind) for t in (1.0, 4.0))
    assert early == late, (early, late)  # static while the camera drifts
    assert early["first"] and early["loaded"] and early["opacity"] == 0.1  # behind everything, decoded, faint
    assert abs((early["left"] + early["right"]) / 2 - width / 2) <= 1
    assert abs((early["top"] + early["bottom"]) / 2 - height / 2) <= 1
    shown = early["right"] - early["left"]
    expected = 0.7 * width if kind == "long-form" else width - 2 * 60 * width / 1080
    assert abs(shown - expected) <= 1, (shown, expected)


COVER = """() => {
  const image = document.querySelector('.backdrop'), veil = document.querySelector('.scrim'), r = image.getBoundingClientRect();
  return {left: r.left, right: r.right, top: r.top, bottom: r.bottom, opacity: +getComputedStyle(image).opacity,
          fit: getComputedStyle(image).objectFit, first: document.getElementById('stage').firstElementChild === image,
          scrim: veil && image.nextElementSibling === veil ? getComputedStyle(veil).backgroundImage : null};
}"""


@pytest.mark.parametrize("kind", ["long-form", "short"])
def test_a_cover_backdrop_fills_the_frame_still_under_its_scrim(tmp_path, tools, kind):
    # Owner, #28 gate 3 (fourth review): a dim test lab photo behind the slides, not the wordmark.
    width, height = render.SIZES[kind]
    photo = tmp_path / "backdrop.jpg"
    ffmpeg("-f", "lavfi", "-i", "color=c=0x202830:s=1600x900,noise=alls=40:allf=t", "-frames:v", "1", str(photo))
    (tmp_path / "branding").mkdir()
    (tmp_path / "branding" / "backdrop.jpg").write_bytes(photo.read_bytes())
    config = CONFIG | {"background": {"image": "branding/backdrop.jpg", "opacity": 0.35, "fit": "cover"}}
    cues = render.scene_cues(SCENES[0], 2, [], 4.0, (width, height), config, None) | render.backdrop(config, tmp_path)
    early, late = (evaluate(cues, t, COVER, kind) for t in (1.0, 4.0))
    assert early == late, (early, late)  # static while the camera drifts
    assert (early["left"], early["top"], early["right"], early["bottom"]) == (0, 0, width, height)
    assert early["fit"] == "cover" and early["first"] and early["opacity"] == 0.35
    assert early["scrim"] and early["scrim"].startswith("linear-gradient"), early


KIT_STATE = """() => {
  const box = e => { const r = e.getBoundingClientRect(); return {top: r.top, bottom: r.bottom, left: r.left, right: r.right}; };
  const look = e => ({...box(e), opacity: +getComputedStyle(e).opacity, width: e.scrollWidth, inner: e.clientWidth});
  return {card: box(document.getElementById('card')), rows: [...document.querySelectorAll('.row')].map(look),
          uses: [...document.querySelectorAll('.use')].map(look), takeaways: [...document.querySelectorAll('.takeaway')].map(look),
          snippet: document.querySelectorAll('.snippet').length};
}"""


@pytest.mark.parametrize("kind", ["long-form", "short"])
def test_a_kit_lights_only_the_current_file_with_its_use_beside_the_card(tools, kind):
    # Owner, #28 gate 3 (fourth review): the same GitHub animation, each part explained with how to use it.
    scene = NEW_KINDS["kit"][0]
    width, height = render.SIZES[kind]
    cues = render.staggered(render.scene_cues(scene, 14, [], 12.0, (width, height), CONFIG, None))
    second = cues["files"][1]["at"]
    state = evaluate(cues, second + 0.8, KIT_STATE, kind)
    card, rows, uses = state["card"], state["rows"], state["uses"]
    assert state["snippet"] == 0 and len(uses) == 4
    # Rows: AGENTS.md, skills/, SKILL.md, scripts/, two scripts; the second file's rows (skills/, SKILL.md) are lit.
    assert [r["opacity"] for r in rows[1:3]] == [1, 1] and rows[0]["opacity"] < 0.6 and rows[4]["opacity"] < 0.6
    assert uses[1]["opacity"] == 1 and uses[0]["opacity"] == 0 and uses[2]["opacity"] == 0
    use = uses[1]
    assert 0 <= use["left"] and use["right"] <= width and use["width"] <= use["inner"] + 1, use
    floor = render.CAPTION_TOP * height if kind == "short" else height
    assert use["bottom"] <= floor and card["bottom"] <= floor, (use, card)
    if kind == "long-form":  # beside the card, level with its row
        assert use["left"] >= card["right"] and use["top"] <= (rows[2]["top"] + rows[2]["bottom"]) / 2 <= use["bottom"]
    else:  # below the card
        assert use["top"] >= card["bottom"], (use, card)
    end = evaluate(cues, cues["seconds"] - render.FADE - 0.05, KIT_STATE, kind)
    assert all(t["opacity"] == 1 and t["bottom"] <= floor and t["right"] <= width for t in end["takeaways"]), end
    assert all(u["opacity"] == 0 for u in end["uses"]) and all(r["opacity"] < 0.6 for r in end["rows"])


MOVES = """() => [...document.querySelectorAll('.action')].map(a => {
  const moving = a.querySelector('.pill, svg'), style = getComputedStyle(moving);
  return {transform: style.transform, background: style.backgroundColor, text: moving.textContent,
          fill: moving.querySelector('path') ? getComputedStyle(moving.querySelector('path')).fill : null,
          logo: document.querySelectorAll('img:not(.backdrop)').length};
})"""


def test_cta_icons_each_do_one_short_move_then_rest_and_the_pill_is_deep_red(tools):
    # Owner, #28 gate 3 (fourth review): like, share, subscribe, notification graphics, each animated as named.
    scene = NEW_KINDS["cta"][0]
    cues = render.staggered(render.scene_cues(scene, 15, [], 8.0, render.SIZES["long-form"], CONFIG, None))
    starts = [a["at"] + render.MOTION["enter"] for a in cues["actions"]]
    middle = [evaluate(cues, t + 0.17, MOVES)[i] for i, t in enumerate(starts)]
    rest = evaluate(cues, cues["seconds"] - render.FADE - 0.05, MOVES)
    assert all(m["transform"] not in ("none", "matrix(1, 0, 0, 1, 0, 0)") for m in middle), middle
    assert all(r["transform"] in ("none", "matrix(1, 0, 0, 1, 0, 0)") for r in rest), rest
    pill = rest[2]
    assert pill["text"] == "Subscribe" and pill["background"] == "rgb(255, 59, 59)", pill  # CONFIG palette syntax
    assert rest[0]["fill"] == "rgb(0, 229, 255)" and rest[0]["logo"] == 0  # the thumb lit in the accent, no logo


HOOK_STATE = """() => {
  const hook = document.querySelector('.hook'), span = document.createRange(), r = hook.getBoundingClientRect();
  span.selectNodeContents(hook);
  const text = span.getBoundingClientRect();
  return {opacity: +getComputedStyle(hook).opacity, top: text.top, bottom: text.bottom, left: text.left, right: text.right,
          size: parseFloat(getComputedStyle(hook).fontSize),
          panels: [...document.querySelectorAll('.side')].map(s => getComputedStyle(s).transform)};
}"""


@pytest.mark.parametrize("kind", ["long-form", "short"])
def test_a_split_hook_shows_big_from_the_first_frame_then_leaves_as_the_panels_come_forward(tools, kind):
    # Owner, #28 gate 3 (fourth review): curiosity and interest in the Short's first 3 seconds.
    scene, code, _ = NEW_KINDS["split"]
    scene = scene | {"hook": "This test has never failed", "say": "This test has never failed. // Spot the bug."}
    words = [
        {"word": w, "start": i * 0.3, "end": i * 0.3 + 0.3}
        for i, w in enumerate(render.WORD.findall("this test has never failed spot the bug"))
    ]
    width, height = render.SIZES[kind]
    cues = render.staggered(render.scene_cues(scene, 1, words, 3.0, (width, height), CONFIG, code))
    until = cues["hook"]["until"]
    first, gone = (
        evaluate(cues, 0.4, HOOK_STATE, kind),
        evaluate(cues, until + render.MOTION["enter"] + 0.05, HOOK_STATE, kind),
    )
    floor = render.CAPTION_TOP * height if kind == "short" else height
    assert first["opacity"] == 1 and first["size"] >= 100 and first["bottom"] <= floor and first["right"] <= width, (
        first
    )
    assert all(t != "none" for t in first["panels"]), first  # the split sits back under the hook
    assert gone["opacity"] == 0 and all(t in ("none", "matrix(1, 0, 0, 1, 0, 0)") for t in gone["panels"]), gone
