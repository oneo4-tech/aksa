"""Tests for the design-thumbnail skill's scripts/thumbnail.py, through main with a fake Gemini and a fake Chrome."""

import base64
import html
import json
import re
import struct
import sys
import zlib
from pathlib import Path

import pytest
from test_youtube_channel import CONFIG, edited, workspace

# A script serving one skill stays in the skill (components.md), outside the pytest pythonpath.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agentic/skills/content/design-thumbnail/scripts"))
import thumbnail

KEY = "fake-key-not-real"
TEXT = "Which test lies?"
SUBJECT = "a smug red bug behind a glowing green checkmark"
# Content issue #38's demo test, reflowed to at most CODE_CHARS characters a line; line 4 is the bug.
CODE = """def test_apply_discount():
  with patch.object(
    discount,
    "apply_discount",
    return_value=90.0,
  ) as fake:
    result = discount\\
      .apply_discount(100, 10)
  assert result == 90.0
"""


def png(width=4, height=4):
    """A tiny valid RGB PNG, so no binary fixture is needed."""

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))

    rows = b"".join(b"\0" + b"\x0f\x0f\x0f" * width for _ in range(height))
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b"")


ART = png()


def answer(data=ART, mime="image/png"):
    """A generateContent response holding one inline image."""
    image = {"inlineData": {"mimeType": mime, "data": base64.b64encode(data).decode()}}
    return {"candidates": [{"content": {"parts": [{"text": "Here it is."}, image]}}]}


class Fakes:
    """Gemini answering with the art (or raising), Chrome returning bytes sized per format, ffmpeg the grey pixels."""

    def __init__(self, response=None, error=None, sizes=None, grey=None):
        self.response, self.error = response or answer(), error
        self.sizes = sizes or {}  # (format, quality) -> byte count of the screenshot
        self.pixels = grey  # the art as GRID x GRID grey pixels, or None as when ffmpeg fails
        self.bodies, self.keys, self.shots = [], [], []

    def post(self, body, key):
        self.bodies.append(body)
        self.keys.append(key)
        if self.error:
            raise self.error
        return self.response

    def shoot(self, page, size, fmt, quality):
        self.shots.append({"page": page, "size": size, "format": fmt, "quality": quality})
        return b"x" * self.sizes.get((fmt, quality), 1000)

    def grey(self, art):
        return self.pixels


@pytest.fixture
def fonts(tmp_path, monkeypatch):
    folder = tmp_path / "fonts"
    folder.mkdir()
    for name in thumbnail.FONTS.values():
        (folder / name).write_bytes(b"font bytes")
    monkeypatch.setenv(thumbnail.FONTS_VARIABLE, str(folder))
    monkeypatch.setenv(thumbnail.KEY_VARIABLE, KEY)
    return folder


def video(root, number=14, title="Spot the Bug: This Test Passes and Checks Nothing"):
    """The video folder with its script.json, whose title says whether the video is about AI."""
    folder = workspace(root) / "videos" / str(number)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "script.json").write_text(json.dumps({"title": title, "scenes": []}))
    return folder


def run(root, fakes, capsys, number=14, text=TEXT, subject=SUBJECT, extra=()):
    texts = [text] if isinstance(text, str) else text
    argv = ["example", str(number), *[a for t in texts for a in ("--text", t)]]
    argv += [*(["--subject", subject] if subject is not None else []), *extra]
    code = thumbnail.main(argv, post=fakes.post, shoot=fakes.shoot, grey=fakes.grey, root=root)
    out = capsys.readouterr()
    return code, out.out, out.err


def test_main_writes_the_thumbnail_at_the_youtube_size(tmp_path, fonts, capsys):
    folder = video(tmp_path)
    fakes = Fakes()
    code, out, _ = run(tmp_path, fakes, capsys)
    assert code == 0
    assert [shot["size"] for shot in fakes.shots] == [(3840, 2160)]
    assert (folder / "thumbnail.png").read_bytes() == b"x" * 1000
    report = json.loads(out)
    assert report["width"] == 3840 and report["height"] == 2160
    assert report["file"] == "thumbnail.png"
    assert report["format"] == "png" and report["bytes"] == 1000
    assert report["text"] == TEXT


@pytest.mark.parametrize(
    ("layout", "place", "aspect"),
    [
        ("split", "right two-thirds", "16:9"),
        ("big-subject", "close up in the left two-thirds", "16:9"),
        ("face-off", "one in each half", "16:9"),
        ("spot-the-bug", "centred", "1:1"),
    ],
)
def test_art_prompt_follows_the_text_overlay_template_in_the_channel_style(
    tmp_path, fonts, capsys, layout, place, aspect
):
    video(tmp_path)
    fakes = Fakes()
    assert run(tmp_path, fakes, capsys, extra=layout_args(tmp_path, layout))[0] == 0
    [body] = fakes.bodies
    prompt = body["contents"][0]["parts"][0]["text"]
    assert prompt.startswith(CONFIG["thumbnail"]["art_style"])
    assert SUBJECT in prompt and place in prompt
    for part in ["clearly readable", "rim light", "saturated", "empty", "gradient", "negative space", "overlaid later"]:
        assert part in prompt
    assert "Plain, unmarked surfaces; blank background." in prompt
    assert not re.search(r"\b(no|not|don't|never)\b", prompt, re.IGNORECASE)
    assert CONFIG["palette"]["background"] not in prompt and "#" not in prompt
    assert prompt.endswith(f"Aspect ratio {aspect}.")
    assert body["generationConfig"]["responseModalities"] == ["IMAGE"]
    assert body["generationConfig"]["imageConfig"]["aspectRatio"] == aspect
    assert fakes.keys == [KEY]


def code_file(root, text=CODE):
    path = root / "code.txt"
    path.write_text(text)
    return path


def code_args(root, mark=4, text=CODE):
    return ["--layout", "spot-the-bug", "--code", str(code_file(root, text)), "--mark", str(mark)]


def layout_args(root, layout):
    return code_args(root) if layout == "spot-the-bug" else ["--layout", layout]


@pytest.mark.parametrize(("number", "layout"), [(12, "split"), (13, "big-subject"), (14, "split"), (15, "big-subject")])
def test_layout_rotates_by_issue_number(tmp_path, fonts, capsys, number, layout):
    video(tmp_path, number)
    fakes = Fakes()
    code, out, _ = run(tmp_path, fakes, capsys, number=number)
    assert code == 0
    assert json.loads(out)["layout"] == layout
    assert f'data-layout="{layout}"' in fakes.shots[0]["page"]


def test_layout_option_overrides_the_rotation(tmp_path, fonts, capsys):
    video(tmp_path, 12)
    fakes = Fakes()
    code, out, _ = run(tmp_path, fakes, capsys, number=12, extra=["--layout", "face-off"])
    assert code == 0
    assert json.loads(out)["layout"] == "face-off"
    assert 'data-layout="face-off"' in fakes.shots[0]["page"]


@pytest.mark.parametrize("layout", thumbnail.LAYOUTS)
def test_page_holds_the_exact_text_escaped_with_the_palette_fonts_and_cropped_art(tmp_path, fonts, capsys, layout):
    video(tmp_path)
    fakes = Fakes()
    text = 'Mocks <b>Lie</b> & "Pass"?'
    assert run(tmp_path, fakes, capsys, text=text, extra=layout_args(tmp_path, layout))[0] == 0
    page = fakes.shots[0]["page"]
    lines = thumbnail.lines(text, layout)
    assert " ".join(lines) == text
    for line in lines:
        assert f'<span class="line">{html.escape(line)}</span>' in page
    assert "<b>" not in page
    assert "{{" not in page
    for colour in CONFIG["palette"].values():
        assert colour in page
    assert "@font-face" in page and "http" not in page
    assert f"data:image/png;base64,{base64.b64encode(ART).decode()}" in page


@pytest.mark.parametrize(
    ("text", "subject"),
    [
        ("Can you spot it now?", SUBJECT),
        ("Alone?", SUBJECT),
        ("Two\nlines?", SUBJECT),
        ("  ", SUBJECT),
        (TEXT, " "),
        (TEXT, None),
    ],
)
def test_bad_text_or_subject_is_refused_without_a_call(tmp_path, fonts, capsys, text, subject):
    video(tmp_path)
    fakes = Fakes()
    code, _, err = run(tmp_path, fakes, capsys, text=text, subject=subject)
    assert code == 2
    assert "error:" in err
    assert fakes.bodies == [] and fakes.shots == []


def test_missing_video_folder_is_refused(tmp_path, fonts, capsys):
    workspace(tmp_path)
    code, _, err = run(tmp_path, Fakes(), capsys)
    assert code == 2
    assert "videos/14" in err


def test_cached_art_is_reused_without_a_second_call(tmp_path, fonts, capsys):
    folder = video(tmp_path)
    fakes = Fakes()
    assert run(tmp_path, fakes, capsys)[0] == 0
    code, out, _ = run(tmp_path, fakes, capsys, text="Is green tested?", extra=["--layout", "split"])
    assert code == 0
    assert len(fakes.bodies) == 1
    assert json.loads(out)["art"] == "cached"
    assert (folder / "thumbnail" / "art-1.png").read_bytes() == ART
    assert len(fakes.shots) == 2


def test_cached_art_reused_without_a_key(tmp_path, fonts, capsys, monkeypatch):
    video(tmp_path)
    fakes = Fakes()
    assert run(tmp_path, fakes, capsys)[0] == 0
    monkeypatch.delenv(thumbnail.KEY_VARIABLE)
    assert run(tmp_path, fakes, capsys)[0] == 0
    assert len(fakes.bodies) == 1


def test_new_subject_with_cached_art_is_refused_unless_new_art_is_asked(tmp_path, fonts, capsys):
    folder = video(tmp_path)
    fakes = Fakes()
    assert run(tmp_path, fakes, capsys)[0] == 0
    code, _, err = run(tmp_path, fakes, capsys, subject="a robot stamping tests green")
    assert code == 3
    assert "--new-art" in err
    assert len(fakes.bodies) == 1
    fakes.response = answer(png(2, 2))
    code, out, _ = run(tmp_path, fakes, capsys, subject="a robot stamping tests green", extra=["--new-art"])
    assert code == 0
    assert len(fakes.bodies) == 2
    assert json.loads(out)["art"] == "generated"
    assert (folder / "thumbnail" / "art-1.png").read_bytes() == png(2, 2)


def test_jpeg_art_is_cached_and_embedded_with_its_type(tmp_path, fonts, capsys):
    folder = video(tmp_path)
    fakes = Fakes(response=answer(b"jpeg bytes", "image/jpeg"))
    assert run(tmp_path, fakes, capsys)[0] == 0
    assert (folder / "thumbnail" / "art-1.jpg").read_bytes() == b"jpeg bytes"
    assert f"data:image/jpeg;base64,{base64.b64encode(b'jpeg bytes').decode()}" in fakes.shots[0]["page"]


def test_missing_key_fails_naming_the_variable(tmp_path, fonts, capsys, monkeypatch):
    video(tmp_path)
    monkeypatch.delenv(thumbnail.KEY_VARIABLE)
    fakes = Fakes()
    code, _, err = run(tmp_path, fakes, capsys)
    assert code == 1
    assert thumbnail.KEY_VARIABLE in err
    assert fakes.bodies == []


@pytest.mark.parametrize(
    ("fakes", "message"),
    [
        (Fakes(error=thumbnail.ApiError("HTTP 400: API key not valid")), "HTTP 400"),
        (Fakes(response={"candidates": [{"content": {"parts": [{"text": "I cannot draw that."}]}}]}), "no image"),
        (Fakes(response={"promptFeedback": {"blockReason": "SAFETY"}}), "no image"),
    ],
)
def test_gemini_error_fails_without_printing_the_key(tmp_path, fonts, capsys, fakes, message):
    folder = video(tmp_path)
    code, out, err = run(tmp_path, fakes, capsys)
    assert code == 1
    assert message in err
    assert KEY not in out + err
    assert not (folder / "thumbnail").exists()
    assert fakes.shots == []


def test_png_over_the_upload_limit_falls_back_to_jpeg_and_removes_the_stale_file(tmp_path, fonts, capsys):
    folder = video(tmp_path)
    (folder / "thumbnail.png").write_bytes(b"old")
    big = thumbnail.LIMIT + 1
    fakes = Fakes(sizes={("png", None): big, ("jpeg", 92): big, ("jpeg", 85): 1_500_000})
    code, out, _ = run(tmp_path, fakes, capsys)
    assert code == 0
    report = json.loads(out)
    assert report["file"] == "thumbnail.jpg" and report["format"] == "jpeg" and report["quality"] == 85
    assert (folder / "thumbnail.jpg").stat().st_size == 1_500_000
    assert not (folder / "thumbnail.png").exists()


def test_thumbnail_too_big_in_every_format_fails(tmp_path, fonts, capsys):
    folder = video(tmp_path)
    big = thumbnail.LIMIT + 1
    fakes = Fakes(sizes={candidate: big for candidate in thumbnail.FORMATS})
    code, _, err = run(tmp_path, fakes, capsys)
    assert code == 1
    assert "2 MB" in err
    assert not (folder / "thumbnail.png").exists() and not (folder / "thumbnail.jpg").exists()


# Content issue #38's art, 1024 pixels square: a red bug at the left and two green checkmarks right of centre.
ART_SIDE = 1024
BUG = (140, 640, 260, 720)
CHECKMARKS = (260, 340, 875, 700)
SUBJECT_BOX = (140, 340, 875, 720)


def opaque(x, y, size):
    """The art's area left unfaded by the mask: the crop less FEATHER of its side at each edge, in art shares."""
    edge = size / 2 - thumbnail.FEATHER * size
    return x - edge, y - edge, x + edge, y + edge


def inside(box, area):
    shares = [value / ART_SIDE for value in box]
    return area[0] <= shares[0] and area[1] <= shares[1] and shares[2] <= area[2] and shares[3] <= area[3]


def test_crop_keeps_an_off_centre_subject_inside_the_opaque_area():
    area = opaque(*thumbnail.crop_for(SUBJECT_BOX, (ART_SIDE, ART_SIDE)))
    assert inside(BUG, area)
    assert inside(CHECKMARKS, area)


def test_crop_of_a_small_centred_subject_is_the_centred_default_view():
    assert thumbnail.crop_for((412, 412, 612, 612), (ART_SIDE, ART_SIDE)) == (0.5, 0.5, thumbnail.CROP)


def grid(background=15, subject=None, value=200):
    """GRID x GRID grey pixels of background, subject (left, top, right, bottom in grid pixels) in value."""
    size = thumbnail.GRID
    left, top, right, bottom = subject or (0, 0, 0, 0)
    return bytes(
        value if left <= x < right and top <= y < bottom else background for y in range(size) for x in range(size)
    )


def test_art_is_cropped_to_its_subject_and_the_report_shows_the_crop(tmp_path, fonts, capsys):
    video(tmp_path)
    scale = thumbnail.GRID / ART_SIDE
    fakes = Fakes(grey=grid(subject=tuple(round(v * scale) for v in SUBJECT_BOX)))
    code, out, _ = run(tmp_path, fakes, capsys, extra=code_args(tmp_path))
    assert code == 0
    crop = json.loads(out)["crop"]
    assert crop["source"] == "subject"
    assert inside(BUG, opaque(crop["x"], crop["y"], crop["size"]))
    page = fakes.shots[0]["page"]
    assert f"--x: {crop['x']}; --y: {crop['y']}; --crop: {crop['size']};" in page


@pytest.mark.parametrize(
    "pixels", [None, grid(), grid(value=30, subject=(10, 10, 20, 20))], ids=["failed", "blank", "faint"]
)
def test_art_without_a_found_subject_keeps_the_centred_crop(tmp_path, fonts, capsys, pixels):
    video(tmp_path)
    fakes = Fakes(grey=pixels)
    code, out, _ = run(tmp_path, fakes, capsys, extra=code_args(tmp_path))
    assert code == 0
    assert json.loads(out)["crop"] == {"x": 0.5, "y": 0.5, "size": thumbnail.CROP, "source": "centred"}
    assert f"--x: 0.5; --y: 0.5; --crop: {thumbnail.CROP};" in fakes.shots[0]["page"]


@pytest.mark.parametrize("layout", ["split", "big-subject", "face-off"])
def test_wide_layouts_show_the_whole_art_without_a_crop(tmp_path, fonts, capsys, layout):
    video(tmp_path)
    fakes = Fakes(grey=grid(subject=(10, 10, 20, 20)))
    code, out, _ = run(tmp_path, fakes, capsys, extra=["--layout", layout])
    assert code == 0
    assert json.loads(out)["crop"] == {"x": 0.5, "y": 0.5, "size": 1, "source": "full"}


@pytest.mark.parametrize(
    ("layout", "lines"), [("split", ["Which", "test", "lies?"]), ("face-off", ["Which test", "lies?"])]
)
def test_text_stacks_a_word_a_line_and_face_off_splits_it_in_halves(layout, lines):
    assert thumbnail.lines(TEXT, layout) == lines


def test_spot_the_bug_shows_the_code_an_ai_chip_and_the_marked_line_without_art(tmp_path, fonts, capsys):
    video(tmp_path)
    fakes = Fakes()
    code, out, _ = run(tmp_path, fakes, capsys, subject=None, extra=code_args(tmp_path, mark=4))
    assert code == 0
    assert fakes.bodies == []
    report = json.loads(out)
    assert report["layout"] == "spot-the-bug" and report["art"] == "none"
    assert report["marker"] == thumbnail.DEFAULT_MARKER
    page = fakes.shots[0]["page"]
    lines = CODE.splitlines()
    for number, line in enumerate(lines, 1):
        if number != 4:
            assert f'<span class="code-line">{html.escape(line)}</span>' in page
    marked = f'<span class="code-line marked">    <span class="bad">{html.escape(lines[3].lstrip())}</span><svg'
    assert marked in page
    assert page.count('class="bug"') == 1
    assert f'<span class="chip-text">{thumbnail.DEFAULT_CHIP}</span>' in page
    assert f'data-marker="{thumbnail.DEFAULT_MARKER}"' in page
    assert "--mark: 4; --lines: 9;" in page
    assert 'class="art"' not in page and "ring" not in page


@pytest.mark.parametrize("marker", thumbnail.MARKERS)
def test_spot_the_bug_draws_the_chosen_marker_and_its_contrast_passes(tmp_path, fonts, capsys, marker):
    video(tmp_path)
    fakes = Fakes()
    code, out, _ = run(tmp_path, fakes, capsys, subject=None, extra=[*code_args(tmp_path), "--marker", marker])
    assert code == 0
    report = json.loads(out)
    assert report["marker"] == marker
    assert f'data-marker="{marker}"' in fakes.shots[0]["page"]
    contrast = report["legibility"]["contrast"]
    assert contrast[marker] >= 3 and contrast["line"] >= 4.5


@pytest.mark.parametrize(
    ("chip", "shown"), [("Copied from docs", "Copied from docs"), ("<AI> & me", "&lt;AI&gt; &amp; me")]
)
def test_chip_text_replaces_the_default_escaped(tmp_path, fonts, capsys, chip, shown):
    video(tmp_path)
    fakes = Fakes()
    code, _, _ = run(tmp_path, fakes, capsys, subject=None, extra=[*code_args(tmp_path), "--chip", chip])
    assert code == 0
    assert f'<span class="chip-text">{shown}</span>' in fakes.shots[0]["page"]


def test_empty_chip_hides_it(tmp_path, fonts, capsys):
    video(tmp_path)
    fakes = Fakes()
    assert run(tmp_path, fakes, capsys, subject=None, extra=[*code_args(tmp_path), "--chip", ""])[0] == 0
    assert 'class="chip"' not in fakes.shots[0]["page"]


@pytest.mark.parametrize(
    ("extra", "message"),
    [
        (["--marker", "highlight"], "--marker"),
        (["--chip", "Written by AI"], "--chip"),
        (lambda root: [*code_args(root), "--chip", "x" * 21], "--chip"),
    ],
    ids=["marker-elsewhere", "chip-elsewhere", "chip-too-long"],
)
def test_marker_and_chip_belong_to_spot_the_bug(tmp_path, fonts, capsys, extra, message):
    video(tmp_path)
    fakes = Fakes()
    code, _, err = run(tmp_path, fakes, capsys, extra=extra(tmp_path) if callable(extra) else extra)
    assert code == 2 and message in err
    assert fakes.bodies == [] and fakes.shots == []


@pytest.mark.parametrize("text", ["Never fails", "Tests Check Nothing", "Mocks lie."])
def test_text_that_does_not_challenge_the_viewer_is_refused(tmp_path, fonts, capsys, text):
    video(tmp_path)
    fakes = Fakes()
    code, _, err = run(tmp_path, fakes, capsys, text=text)
    assert code == 2
    assert "challenge" in err and "?" in err and "spot" in err
    assert fakes.bodies == [] and fakes.shots == []


@pytest.mark.parametrize("text", ["Will this fail?", "Spot the bug", "Can you SPOT it", "Find it!"])
def test_text_ending_in_a_question_or_using_a_challenge_verb_passes(tmp_path, fonts, capsys, text):
    video(tmp_path)
    assert run(tmp_path, Fakes(), capsys, text=text)[0] == 0


AI_TITLE = "Spot the Bug: This AI Test Passes and Tests Nothing"


@pytest.mark.parametrize(
    ("text", "subject", "extra"),
    [
        ("Will this fail?", SUBJECT, []),
        ("Will this fail?", None, ["--chip", ""]),
        ("Will it fail?", "a smug detail of a trap", []),
    ],
    ids=["split", "spot-the-bug-without-chip", "unrelated-subject"],
)
def test_video_about_ai_without_an_ai_cue_is_refused(tmp_path, fonts, capsys, text, subject, extra):
    video(tmp_path, title=AI_TITLE)
    fakes = Fakes()
    extra = [*code_args(tmp_path), *extra] if subject is None else extra
    code, _, err = run(tmp_path, fakes, capsys, text=text, subject=subject, extra=extra)
    assert code == 2
    assert "AI" in err and "--chip" in err
    assert fakes.bodies == [] and fakes.shots == []


@pytest.mark.parametrize(
    ("text", "subject", "spot"),
    [
        ("Will AI catch this?", SUBJECT, False),
        ("Will this fail?", "a nervous clay robot hiding a bug", False),
        ("Can you spot it?", None, True),
    ],
    ids=["text", "subject", "default-chip"],
)
def test_video_about_ai_passes_with_ai_in_the_text_subject_or_chip(tmp_path, fonts, capsys, text, subject, spot):
    video(tmp_path, title=AI_TITLE)
    code, out, _ = run(tmp_path, Fakes(), capsys, text=text, subject=subject, extra=code_args(tmp_path) if spot else [])
    assert code == 0
    assert json.loads(out)["about_ai"] is True


def test_video_without_a_script_is_refused(tmp_path, fonts, capsys):
    folder = video(tmp_path)
    (folder / "script.json").unlink()
    fakes = Fakes()
    code, _, err = run(tmp_path, fakes, capsys)
    assert code == 2
    assert "script.json" in err and "write-video-script" in err
    assert fakes.bodies == [] and fakes.shots == []


@pytest.mark.parametrize(
    ("extra", "message"),
    [
        (["--layout", "spot-the-bug"], "--code"),
        (lambda root: ["--code", str(code_file(root)), "--mark", "4"], "spot-the-bug"),
        (lambda root: code_args(root, text="x = 1\n" * 5), "6 to 10 lines"),
        (lambda root: code_args(root, text="x = 1\n" * 11), "6 to 10 lines"),
        (lambda root: code_args(root, text="x = 1\n" * 6 + "y" * 31 + "\n"), "30 characters"),
        (lambda root: code_args(root, mark=10), "--mark"),
        (lambda root: code_args(root, mark=0), "--mark"),
    ],
    ids=["no-code", "code-elsewhere", "few-lines", "many-lines", "long-line", "mark-past-end", "mark-zero"],
)
def test_bad_code_is_refused_without_a_call(tmp_path, fonts, capsys, extra, message):
    video(tmp_path)
    fakes = Fakes()
    code, _, err = run(tmp_path, fakes, capsys, extra=extra(tmp_path) if callable(extra) else extra)
    assert code == 2
    assert message in err
    assert fakes.bodies == [] and fakes.shots == []


def test_page_sets_the_least_text_size_for_a_cap_height_of_15_percent(tmp_path, fonts, capsys):
    video(tmp_path)
    fakes = Fakes()
    code, out, _ = run(tmp_path, fakes, capsys)
    assert code == 0
    least = thumbnail.MIN_TEXT_PX
    assert least * thumbnail.CAP_HEIGHT >= 0.15 * 720 > (least - 1) * thumbnail.CAP_HEIGHT
    assert f"--min-text: {least}px;" in fakes.shots[0]["page"]
    assert json.loads(out)["legibility"]["cap_height"] >= 0.15


def test_report_shows_the_text_and_marker_contrast_on_the_field(tmp_path, fonts, capsys):
    video(tmp_path)
    code, out, _ = run(tmp_path, Fakes(), capsys)
    assert code == 0
    contrast = json.loads(out)["legibility"]["contrast"]
    assert contrast["text"] >= 4.5 and contrast["key"] >= 4.5 and contrast["marker"] >= 3


@pytest.mark.parametrize(("colour", "value"), [("name", "#3A3A3A"), ("suffix", "#2020A0"), ("syntax", "#F0F0F0")])
def test_palette_below_the_contrast_rules_is_refused(tmp_path, fonts, capsys, colour, value):
    video(tmp_path)
    workspace(tmp_path, edited(CONFIG, f"palette.{colour}", value))
    fakes = Fakes()
    code, _, err = run(tmp_path, fakes, capsys)
    assert code == 2
    assert "contrast" in err
    assert fakes.bodies == [] and fakes.shots == []


# The field (owner, third gate 3 of #38): grey instead of purple, set by channel.yaml thumbnail.field.

GREY = ["#4A4A4A", "#262626"]


def test_the_field_defaults_to_indigo_and_names_it_in_the_prompt(tmp_path, fonts, capsys):
    video(tmp_path)
    fakes = Fakes()
    assert run(tmp_path, fakes, capsys)[0] == 0
    assert f"--field-1: {thumbnail.FIELD[0]}; --field-2: {thumbnail.FIELD[1]};" in fakes.shots[0]["page"]
    assert "smooth, empty deep indigo-to-violet gradient" in fakes.bodies[0]["contents"][0]["parts"][0]["text"]


def test_a_grey_channel_field_is_drawn_checked_and_named_in_words(tmp_path, fonts, capsys):
    video(tmp_path)
    workspace(tmp_path, edited(CONFIG, "thumbnail.field", GREY))
    fakes = Fakes()
    code, out, _ = run(tmp_path, fakes, capsys)
    assert code == 0
    assert f"--field-1: {GREY[0]}; --field-2: {GREY[1]};" in fakes.shots[0]["page"]
    contrast = json.loads(out)["legibility"]["contrast"]
    assert contrast["text"] == round(min(thumbnail.contrast(CONFIG["palette"]["name"], c) for c in GREY), 2)
    assert contrast["text"] >= 4.5 and contrast["key"] >= 4.5 and contrast["marker"] >= 3
    prompt = fakes.bodies[0]["contents"][0]["parts"][0]["text"]
    assert "smooth, empty dark grey gradient" in prompt and "#" not in prompt and "indigo" not in prompt


@pytest.mark.parametrize(
    ("field", "words"),
    [
        (["#4A4A4A", "#262626"], "dark grey"),
        (["#3A6AD0", "#1E3A80"], "deep blue"),
        (["#2A8A40", "#3A2A9A"], "deep green-to-indigo"),
        (["#C0C0C0", "#A0A0A0"], "light grey"),
    ],
)
def test_field_words_name_the_gradient_without_a_hex_code(field, words):
    assert thumbnail.field_words(tuple(field)) == words


def test_a_channel_field_too_light_for_the_text_is_refused(tmp_path, fonts, capsys):
    video(tmp_path)
    workspace(tmp_path, edited(CONFIG, "thumbnail.field", ["#E0E0E0", "#C0C0C0"]))
    fakes = Fakes()
    code, _, err = run(tmp_path, fakes, capsys)
    assert code == 2 and "palette: text contrast" in err
    assert fakes.bodies == [] and fakes.shots == []


def test_contrast_matches_wcag():
    assert thumbnail.contrast("#000000", "#FFFFFF") == pytest.approx(21)
    assert thumbnail.contrast("#CC0000", "#0F0F0F") == pytest.approx(3.26, abs=0.01)


def test_no_template_sets_text_in_red():
    for path in thumbnail.REFERENCES.iterdir():
        assert "color: var(--red)" not in path.read_text(), path.name


def test_candidates_generate_and_compose_each_art_and_report_the_cost_first(tmp_path, fonts, capsys):
    folder = video(tmp_path)
    fakes = Fakes()
    code, out, err = run(tmp_path, fakes, capsys, extra=["--candidates", "3"])
    assert code == 0
    assert len(fakes.bodies) == 3 and len(fakes.shots) == 3 + 1  # three candidates and the contact sheet
    assert "3 new images, about USD 0.21" in err
    report = json.loads(out)
    assert report["cost_usd"] == 0.21 and report["art"] == "generated"
    assert [c["file"] for c in report["candidates"]] == ["thumbnail-1.png", "thumbnail-2.png", "thumbnail-3.png"]
    for number in (1, 2, 3):
        assert (folder / f"thumbnail-{number}.png").exists()
        assert (folder / "thumbnail" / f"art-{number}.png").read_bytes() == ART
    assert not (folder / "thumbnail.png").exists()


def test_cached_candidates_are_reused_and_only_missing_ones_are_paid(tmp_path, fonts, capsys):
    video(tmp_path)
    fakes = Fakes()
    assert run(tmp_path, fakes, capsys)[0] == 0
    code, out, err = run(tmp_path, fakes, capsys, extra=["--candidates", "3"])
    assert code == 0
    assert len(fakes.bodies) == 3
    assert "2 new images, about USD 0.14" in err
    assert json.loads(out)["cost_usd"] == 0.14
    code, out, err = run(tmp_path, fakes, capsys, extra=["--candidates", "2"])
    assert code == 0
    assert len(fakes.bodies) == 3 and "USD" not in err
    report = json.loads(out)
    assert report["cost_usd"] == 0 and report["art"] == "cached" and len(report["candidates"]) == 2


def test_failed_candidate_keeps_the_art_already_paid_for(tmp_path, fonts, capsys):
    folder = video(tmp_path)
    fakes = Fakes()
    replies = [answer(), thumbnail.ApiError("HTTP 429: quota")]

    def post(body, key):
        fakes.bodies.append(body)
        reply = replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply

    fakes.post = post
    code, _, err = run(tmp_path, fakes, capsys, extra=["--candidates", "2"])
    assert code == 1 and "429" in err
    record = json.loads((folder / "thumbnail" / "art.json").read_text())
    assert record["files"] == [{"file": "art-1.png", "mime": "image/png"}]
    assert (folder / "thumbnail" / "art-1.png").read_bytes() == ART


@pytest.mark.parametrize(
    ("extra", "subject", "message"),
    [(["--candidates", "0"], SUBJECT, "--candidates"), (["--candidates", "4"], SUBJECT, "--candidates")],
)
def test_candidates_outside_one_to_three_are_refused(tmp_path, fonts, capsys, extra, subject, message):
    video(tmp_path)
    fakes = Fakes()
    code, _, err = run(tmp_path, fakes, capsys, subject=subject, extra=extra)
    assert code == 2 and message in err
    assert fakes.bodies == [] and fakes.shots == []


TEXTS = ["Can you spot it?", "AI wrote this. Bug?", "Will this fail?"]


def test_free_candidates_vary_the_text_and_marker_and_make_a_contact_sheet(tmp_path, fonts, capsys):
    folder = video(tmp_path)
    fakes = Fakes()
    markers = [a for m in thumbnail.MARKERS for a in ("--marker", m)]
    extra = [*code_args(tmp_path), *markers, "--candidates", "3"]
    code, out, err = run(tmp_path, fakes, capsys, text=TEXTS, subject=None, extra=extra)
    assert code == 0
    assert fakes.bodies == [] and "USD" not in err
    report = json.loads(out)
    assert report["cost_usd"] == 0 and report["art"] == "none"
    entries = report["candidates"]
    assert [(c["text"], c["marker"]) for c in entries] == list(zip(TEXTS, thumbnail.MARKERS, strict=True))
    assert [c["file"] for c in entries] == ["thumbnail-1.png", "thumbnail-2.png", "thumbnail-3.png"]
    for number, text in enumerate(TEXTS, 1):
        assert (folder / f"thumbnail-{number}.png").exists()
        assert html.escape(text.split()[-1]) in fakes.shots[number - 1]["page"]
    assert report["contact_sheet"] == "thumbnail-candidates.png"
    assert (folder / "thumbnail-candidates.png").exists()
    sheet = fakes.shots[-1]
    assert len(fakes.shots) == 4 and sheet["format"] == "png"
    assert sheet["page"].count(f"data:image/png;base64,{base64.b64encode(b'x' * 1000).decode()}") == 3 * 3
    assert "thumbnail-3" in sheet["page"] and not (folder / "thumbnail.png").exists()


def test_one_text_with_three_markers_makes_three_free_candidates(tmp_path, fonts, capsys):
    video(tmp_path)
    markers = [a for m in thumbnail.MARKERS for a in ("--marker", m)]
    code, out, _ = run(
        tmp_path, Fakes(), capsys, subject=None, extra=[*code_args(tmp_path), *markers, "--candidates", "3"]
    )
    assert code == 0
    assert [c["text"] for c in json.loads(out)["candidates"]] == [TEXT] * 3


@pytest.mark.parametrize(
    ("texts", "subject", "count"),
    [([TEXT], None, "2"), (TEXTS[:2], None, "3"), (TEXTS[:2], SUBJECT, "3"), (TEXTS[:2], SUBJECT, "1")],
    ids=["free-no-variation", "free-too-few", "art-too-few", "one-candidate-two-texts"],
)
def test_candidates_whose_variants_do_not_match_are_refused(tmp_path, fonts, capsys, texts, subject, count):
    video(tmp_path)
    fakes = Fakes()
    extra = [*(code_args(tmp_path) if subject is None else []), "--candidates", count]
    code, _, err = run(tmp_path, fakes, capsys, text=texts, subject=subject, extra=extra)
    assert code == 2 and "--candidates" in err
    assert fakes.bodies == [] and fakes.shots == []


def test_art_candidates_take_one_text_each(tmp_path, fonts, capsys):
    video(tmp_path)
    fakes = Fakes()
    code, out, _ = run(tmp_path, fakes, capsys, text=TEXTS[:2], extra=["--candidates", "2"])
    assert code == 0
    assert [c["text"] for c in json.loads(out)["candidates"]] == TEXTS[:2]
    assert len(fakes.bodies) == 2


def test_pick_makes_the_thumbnail_from_a_candidate_for_free(tmp_path, fonts, capsys):
    folder = video(tmp_path)
    (folder / "thumbnail-1.png").write_bytes(b"one")
    (folder / "thumbnail-2.jpg").write_bytes(b"two")
    (folder / "thumbnail.png").write_bytes(b"old")
    fakes = Fakes()
    code = thumbnail.main(["example", "14", "--pick", "2"], post=fakes.post, shoot=fakes.shoot, root=tmp_path)
    out = capsys.readouterr().out
    assert code == 0
    assert (folder / "thumbnail.jpg").read_bytes() == b"two"
    assert not (folder / "thumbnail.png").exists()
    assert fakes.bodies == [] and fakes.shots == []
    assert json.loads(out) == {"picked": 2, "file": "thumbnail.jpg", "format": "jpeg", "bytes": 3}


@pytest.mark.parametrize("argv", [["--pick", "3"], ["--pick", "1", "--text", TEXT]], ids=["missing", "with-text"])
def test_pick_of_a_missing_candidate_or_with_other_options_is_refused(tmp_path, fonts, capsys, argv):
    folder = video(tmp_path)
    (folder / "thumbnail-1.png").write_bytes(b"one")
    assert thumbnail.main(["example", "14", *argv], root=tmp_path) == 2
    assert "--pick" in capsys.readouterr().err
    assert not (folder / "thumbnail.png").exists()


def test_art_cached_before_candidates_is_still_reused(tmp_path, fonts, capsys):
    folder = video(tmp_path) / "thumbnail"
    folder.mkdir()
    (folder / "art.png").write_bytes(ART)
    record = {"prompt": thumbnail.prompt(SUBJECT, CONFIG, "split"), "file": "art.png", "mime": "image/png"}
    (folder / "art.json").write_text(json.dumps(record))
    fakes = Fakes()
    code, out, _ = run(tmp_path, fakes, capsys)
    assert code == 0
    assert fakes.bodies == [] and json.loads(out)["art"] == "cached"
