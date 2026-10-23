"""Tests for the design-thumbnail skill's scripts/thumbnail.py, through main with a fake Gemini and a fake Chrome."""

import base64
import html
import json
import struct
import sys
import zlib
from pathlib import Path

import pytest
from test_youtube_channel import CONFIG, workspace

# A script serving one skill stays in the skill (components.md), outside the pytest pythonpath.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agentic/skills/content/design-thumbnail/scripts"))
import thumbnail

KEY = "fake-key-not-real"
TEXT = "Tests Check Nothing"
SUBJECT = "a smug red bug behind a glowing green checkmark"


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
    """Gemini answering with the art (or raising), Chrome returning bytes sized per format."""

    def __init__(self, response=None, error=None, sizes=None):
        self.response, self.error = response or answer(), error
        self.sizes = sizes or {}  # (format, quality) -> byte count of the screenshot
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


@pytest.fixture
def fonts(tmp_path, monkeypatch):
    folder = tmp_path / "fonts"
    folder.mkdir()
    for name in thumbnail.FONTS.values():
        (folder / name).write_bytes(b"font bytes")
    monkeypatch.setenv(thumbnail.FONTS_VARIABLE, str(folder))
    monkeypatch.setenv(thumbnail.KEY_VARIABLE, KEY)
    return folder


def video(root, number=14):
    folder = workspace(root) / "videos" / str(number)
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def run(root, fakes, capsys, number=14, text=TEXT, subject=SUBJECT, extra=()):
    argv = ["example", str(number), "--text", text, "--subject", subject, *extra]
    code = thumbnail.main(argv, post=fakes.post, shoot=fakes.shoot, root=root)
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


def test_art_prompt_forbids_text_and_asks_for_the_channel_art_style(tmp_path, fonts, capsys):
    video(tmp_path)
    fakes = Fakes()
    assert run(tmp_path, fakes, capsys)[0] == 0
    [body] = fakes.bodies
    prompt = body["contents"][0]["parts"][0]["text"]
    assert prompt.startswith(CONFIG["thumbnail"]["art_style"])
    assert SUBJECT in prompt
    assert "Absolutely no text, letters, or numbers" in prompt
    assert CONFIG["palette"]["background"] in prompt
    assert body["generationConfig"]["responseModalities"] == ["IMAGE"]
    assert body["generationConfig"]["imageConfig"]["aspectRatio"] == "1:1"
    assert fakes.keys == [KEY]


@pytest.mark.parametrize(
    ("number", "layout"), [(12, "split"), (13, "code-circle"), (14, "face-off"), (15, "split"), (16, "code-circle")]
)
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
    text = 'Mocks <b>Lie</b> & "Pass"'
    assert run(tmp_path, fakes, capsys, text=text, extra=["--layout", layout])[0] == 0
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
    assert f"--crop: {thumbnail.CROP}" in page


@pytest.mark.parametrize(
    ("text", "subject"), [("One two three four five", SUBJECT), ("  ", SUBJECT), (TEXT, " "), ("Two\nlines", SUBJECT)]
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
    code, out, _ = run(tmp_path, fakes, capsys, text="Green Is Not Tested", extra=["--layout", "split"])
    assert code == 0
    assert len(fakes.bodies) == 1
    assert json.loads(out)["art"] == "cached"
    assert (folder / "thumbnail" / "art.png").read_bytes() == ART
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
    assert (folder / "thumbnail" / "art.png").read_bytes() == png(2, 2)


def test_jpeg_art_is_cached_and_embedded_with_its_type(tmp_path, fonts, capsys):
    folder = video(tmp_path)
    fakes = Fakes(response=answer(b"jpeg bytes", "image/jpeg"))
    assert run(tmp_path, fakes, capsys)[0] == 0
    assert (folder / "thumbnail" / "art.jpg").read_bytes() == b"jpeg bytes"
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
    fakes = Fakes(sizes={candidate: big for candidate in thumbnail.CANDIDATES})
    code, _, err = run(tmp_path, fakes, capsys)
    assert code == 1
    assert "2 MB" in err
    assert not (folder / "thumbnail.png").exists() and not (folder / "thumbnail.jpg").exists()
