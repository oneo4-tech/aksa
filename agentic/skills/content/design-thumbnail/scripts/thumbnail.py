"""Design a video's thumbnail: a channel layout holding the exact text, around text-free Gemini art.

Usage: uv run --env-file .env agentic/skills/content/design-thumbnail/scripts/thumbnail.py
         CHANNEL N --text "..." [--text "..."] [--subject "..."] [--layout L]
         [--code FILE --mark K [--marker M] [--chip "..."]] [--candidates N] [--new-art]
       uv run agentic/skills/content/design-thumbnail/scripts/thumbnail.py CHANNEL N --pick K

  --text      the thumbnail text, MIN_WORDS to MAX_WORDS words on one line, shown exactly as given,
              a word a line (face-off: a half a side), the last word the key word in the accent.
              It challenges the viewer: ends with "?" or uses a CHALLENGES verb. Once, or once
              per candidate
  --subject   what the art shows, in words; the prompt adds the style and composition; optional
              only for spot-the-bug
  --layout    split, big-subject, spot-the-bug, or face-off; default ROTATION[N % 2] (split,
              big-subject), so neighbouring videos differ
  --code      spot-the-bug: a file of CODE_LINES lines of the demo's code, each at most CODE_CHARS
  --mark      spot-the-bug: the number of the buggy line in --code
  --marker    spot-the-bug: how the buggy line is marked, MARKERS (default DEFAULT_MARKER: a soft
              accent bar); a small red bug glyph sits in its gutter. Once, or once per candidate
  --chip      spot-the-bug: the code panel's chip, at most CHIP_CHARS characters, default
              DEFAULT_CHIP; empty hides it
  --new-art   pay for new art when the cached art was made from another prompt
  --candidates  1 to MAX_CANDIDATES variants, each composed as thumbnail-<k>, plus the contact
              sheet SHEET; default 1, composed as thumbnail. With --subject each has its own art
              image; without, they are free and differ by --text or --marker, given N times
  --pick      copy candidate K to thumbnail.png or .jpg: free, no Chrome, no other option

Field: the background gradient behind the art and text is channel.yaml thumbnail.field (two
colours), else FIELD (indigo). The prompt names it in words, never a hex code, which an image model
may draw as text: FIELD_WORDS for FIELD, else each colour's hue name (grey under GREY_SATURATION,
else HUES) with a tone, such as "dark grey" or "deep green-to-indigo".

Reads channel.yaml palette, thumbnail.art_style, and thumbnail.field, and writes, in the channel workspace's
videos/<N>/ (which must exist):

  thumbnail/art-<k>.<ext>, art.json  the art images and the prompt they came from: the cache
  thumbnail.png or thumbnail.jpg     the thumbnail, SIZE pixels, under LIMIT bytes
  thumbnail-<k>.png or .jpg          with --candidates over 1, candidate k, the same way
  thumbnail-candidates.png           with --candidates over 1, the candidates side by side at
                                     full, 320 px, and 168 px width, on YouTube's page colour

AI cue: the video's script.json must exist (else exit 2); when its title names AI (AI_WORDS), each
text must name AI, unless the art subject or spot-the-bug's chip does (else exit 2).

Art: one Gemini generateContent request (MODEL, responseModalities IMAGE, aspect ratio 16:9,
or 1:1 for spot-the-bug) with Gemini's template for art with text overlaid later: "<art_style>.
A bold, minimalist composition featuring <subject>, <PLACES: where, how large>, ... rim light ...
a smooth, empty <field in words> gradient, leaving significant negative space toward <PLACES: the
text side> ... Plain, unmarked surfaces; blank background. ... Aspect ratio <ratio>." It costs
about PRICE_USD (USD 0.07) an image (no free tier); before calling, stderr names the count of new
images and their cost. The key is the GEMINI_API_KEY environment variable,
read from .env by uv run --env-file .env; it is never printed. Art made from the same prompt
is reused without a call, so re-composing never pays twice, and asking more candidates pays
only for the missing ones; each image is cached as soon as it is paid for. A different prompt
is refused (exit 3) unless --new-art.

Compose: references/<layout>.html with references/thumbnail.css and references/fit.js, the
palette and the field as CSS variables, the text and code HTML-escaped into their lines,
the art embedded (whole in the wide layouts, cropped to its subject in spot-the-bug), and the Space
Grotesk and Fira Code files embedded (RENDER_FONTS, else .cache/fonts in the home folder;
nothing loads from the network). fit.js shrinks the text until it fits its box.

Legibility: before composing, the text (palette name) and key word (palette suffix) must reach
4.5:1 on both field colours and the red marker (palette syntax) 3:1 on its warm white outline
(WCAG 2.2); in spot-the-bug each marker's colour 3:1 on PANEL and the marked line 4.5:1 on its
highlight; else exit 2. fit.js never shrinks the text below MIN_TEXT_PX, a cap height of MIN_CAP
of the frame height; text that does not fit at that size is refused (exit 2).

Crop (spot-the-bug): image models do not reliably centre the subject, so ffmpeg reads the art
as GRID x GRID grey pixels and the subject is the box of pixels differing by more than
THRESHOLD from the background (the median border pixel). The crop is the square centred on that box holding it
with MARGIN inside the mask's opaque area (the crop less FEATHER of its side at each edge),
never under CROP of the art's side, clamped to the art. No ffmpeg, a failure, or no subject
found: the centred CROP view.

Encode: the system Chrome, through Playwright, shoots the 1280x720 page at 3x for SIZE, as
PNG, else JPEG at falling quality (FORMATS), the first under LIMIT (YouTube's 2 MB upload
limit); the other format's stale file is removed. Prints a JSON report: layout, about_ai, art
(cached, generated, or none), prompt, cost_usd, legibility (cap_height, contrast), width,
height, and the thumbnail's text, marker, crop (x, y, size as shares of the art's side, and
source: subject, centred, or full), file, format, quality, and bytes; with --candidates over 1,
those last seven for each candidate under candidates, and contact_sheet. --pick prints picked,
file, format, and bytes.

Needs Google Chrome and the fonts (README, Setup), and ffmpeg to find the subject; GEMINI_API_KEY
only when art is generated.

Exit codes: 0 written, 1 a Gemini, Chrome, font, or file error, the key missing, or no format
under LIMIT, 2 bad input (an invalid channel, text, subject, or code, a palette under the contrast
rules, text too long for the least cap height, text that does not challenge or lacks the AI
cue, no video folder or script), 3 refused
(cached art from another prompt without --new-art).
"""

import argparse
import base64
import binascii
import colorsys
import html
import json
import math
import os
import re
import string
import subprocess
import sys
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO_ROOT / "agentic" / "scripts"))
import youtube_channel

REFERENCES = Path(__file__).resolve().parents[1] / "references"
MODEL = "gemini-3.1-flash-image"
GENERATE = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
KEY_VARIABLE = "GEMINI_API_KEY"
TIMEOUT_SECONDS = 180
LAYOUTS = ["split", "big-subject", "spot-the-bug", "face-off"]
ROTATION = ["split", "big-subject"]  # the default by issue number; spot-the-bug and face-off when the content fits
MIN_WORDS, MAX_WORDS = 2, 4
# The text challenges the viewer: it ends with "?" or uses one of these verbs (H4: a curiosity gap, not a statement).
CHALLENGES = ("spot", "find", "catch", "guess", "fix", "break", "beat", "prove")
# A video whose script title names AI shows AI on its thumbnail: in the text, the spot-the-bug chip, or the art.
AI_WORDS = re.compile(r"\b(AI|LLMs?|robots?)\b", re.IGNORECASE)
# spot-the-bug: the buggy line's marker; red stays a small accent (the bug glyph, the squiggle), never a big ring.
MARKERS = ("highlight", "squiggle", "underline")
DEFAULT_MARKER = "highlight"
MARKER_COLOURS = {"highlight": "suffix", "squiggle": "syntax", "underline": "suffix"}  # the palette colour each draws
DEFAULT_CHIP, CHIP_CHARS = "Written by AI", 20  # the code panel's header chip: who wrote the code
PANEL = "#0D0B1F"  # the code panel behind the code lines
HIGHLIGHT = 0.22  # share of the accent in the highlight bar, mixed into PANEL
CHIP_ROW = 62  # the chip's height and gap above the code, in canvas pixels
SHEET = "thumbnail-candidates.png"  # the contact sheet of the candidates, at full, 320 px, and 168 px width
SHEET_GAP = 32
# The default field behind the art and text, lighter than YouTube's #0F0F0F page so the thumbnail has an edge;
# channel.yaml thumbnail.field replaces it.
FIELD = ("#3A2A9A", "#1E1660")
CAP_HEIGHT = 0.70  # Space Grotesk's cap height, as a share of its font size (OS/2 sCapHeight 700 of 1000)
MIN_CAP = 0.15  # least cap height of the text, as a share of the frame height
MIN_TEXT_PX = math.ceil(MIN_CAP * 720 / CAP_HEIGHT)  # fit.js never shrinks the text below this on the 720 canvas
TEXT_CONTRAST, MARKER_CONTRAST = 4.5, 3.0  # WCAG 2.2 text and graphical-object minimums
CODE_LINES = (6, 10)
CODE_CHARS = 30  # longest code line: 30 Fira Code characters at 36 px fit the spot-the-bug panel
SQUARE = {"spot-the-bug"}  # layouts showing a square crop of the art; the others show all of it
SIZE = (3840, 2160)  # YouTube's recommended thumbnail size, 16:9
SCALE = 3  # the templates are a 1280x720 canvas
LIMIT = 2_000_000  # YouTube's 2 MB thumbnail upload limit
FORMATS = [("png", None), ("jpeg", 92), ("jpeg", 85), ("jpeg", 75), ("jpeg", 65)]
PRICE_USD = 0.07  # one Gemini 3.1 Flash Image image; the model has no free tier
MAX_CANDIDATES = 3  # YouTube's Test & Compare tries up to 3 thumbnails
CROP = 0.62  # least share of the art's side kept, and the centred view when no subject is found
FEATHER = 0.1  # share of the art box's side faded into the background at each edge (thumbnail.css)
MARGIN = 0.03  # share of the art's side kept clear around the subject
GRID = 64  # the art is read as GRID x GRID grey pixels to find its subject
THRESHOLD = 24  # grey levels by which a subject pixel differs from the background
# The art prompt follows Gemini's template for art with text overlaid later: one subject placed off-centre, an
# empty background leaving negative space, exclusions said positively. Where each layout wants the subject and space.
PLACES = {
    "split": ("placed in the right two-thirds of the frame, filling about 55% of the frame height", "the left third"),
    "big-subject": (
        "shown close up in the left two-thirds of the frame, filling about 60% of its height",
        "the right third",
    ),
    "face-off": (
        "arranged as a face-off, one in each half of the frame, each filling about 55% of its height",
        "the top",
    ),
    "spot-the-bug": ("centred in the frame, filling about 70% of the frame height", "the edges"),
}
FIELD_WORDS = "deep indigo-to-violet"  # FIELD in words: a hex code in a prompt risks being drawn as text
GREY_SATURATION = 0.12  # a field colour under this HLS saturation is named grey
HUES = [
    (15, "red"),
    (40, "orange"),
    (65, "yellow"),
    (160, "green"),
    (195, "teal"),
    (235, "blue"),
    (265, "indigo"),
    (290, "violet"),
    (335, "magenta"),
    (360, "red"),
]  # hue in degrees below which each name applies
TYPES = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}
CHROME_ARGS = ["--disable-gpu", "--force-color-profile=srgb"]
FONTS = {"Space Grotesk": "SpaceGrotesk.ttf", "Fira Code": "FiraCode.ttf"}
FONTS_VARIABLE = "RENDER_FONTS"  # the same fonts render-video uses
FONTS_DIR = Path.home() / ".cache" / "fonts"
# A flat bug glyph for the gutter of spot-the-bug's marked line, coloured by the template's CSS.
BUG = (
    '<svg class="bug" viewBox="0 0 64 64" aria-hidden="true"><path class="legs" d="M18 30 8 24M16 40H5M18 50 9 57'
    'M46 30 56 24M48 40H59M46 50 55 57M27 13 21 5M37 13 43 5"/><circle class="head" cx="32" cy="18" r="9"/>'
    '<ellipse class="body" cx="32" cy="40" rx="17" ry="19"/><path class="seam" d="M32 22V58"/>'
    '<circle class="spot" cx="24" cy="36" r="3.5"/><circle class="spot" cx="40" cy="36" r="3.5"/>'
    '<circle class="spot" cx="25" cy="48" r="3"/><circle class="spot" cx="39" cy="48" r="3"/></svg>'
)
SPARK = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 1c1 7 4 10 11 11-7 1-10 4-11 11-1-7-4-10-11-11 7-1 10-4 11-11Z"/></svg>'
PLACEHOLDERS = ["/*{{fonts}}*/", "/*{{css}}*/", "/*{{palette}}*/", "/*{{js}}*/", "<!--{{art}}-->", "<!--{{text}}-->"]


class BadInput(Exception):
    """Invalid text or subject, or no video folder: exit 2."""


class Refused(Exception):
    """Cached art from another prompt without --new-art: exit 3."""


class ApiError(Exception):
    """Gemini failed or answered without an image, or the key is missing: exit 1. Never holds the key."""


class ToolError(Exception):
    """Chrome, a font, or a template missing or failing, or no format under LIMIT: exit 1."""


def challenges(text: str) -> bool:
    """Whether the text puts a challenge or question to the viewer: it ends with "?" or uses a CHALLENGES verb."""
    words = [word.strip(string.punctuation).lower() for word in text.split()]
    return text.rstrip().endswith("?") or any(word in CHALLENGES for word in words)


def text_problems(texts: list[str], subject: str | None, layout: str) -> list[str]:
    problems = []
    for text in texts:
        if "\n" in text or not MIN_WORDS <= len(text.split()) <= MAX_WORDS:
            problems.append(f"--text {text!r}: must be {MIN_WORDS} to {MAX_WORDS} words on one line")
        elif not challenges(text):
            problems.append(
                f'--text {text!r}: must challenge the viewer: end with "?" or use one of {", ".join(CHALLENGES)}'
            )
    if (subject is not None or layout not in SQUARE) and not (subject or "").strip():
        problems.append("--subject: must say what the art shows (optional only for spot-the-bug)")
    return problems


def ai_problems(title: str, texts: list[str], subject: str | None, chip: str) -> list[str]:
    """What lacks an AI cue when the script's title names AI: each text needs AI in itself, the chip, or the art."""
    if not AI_WORDS.search(title) or AI_WORDS.search(f"{subject or ''} {chip}"):
        return []
    return [
        f"--text {text!r}: the video is about AI ({title!r}), so the thumbnail must show it: name AI in the text, "
        f'keep the spot-the-bug chip (--chip "{DEFAULT_CHIP}"), or show an AI character in --subject'
        for text in texts
        if not AI_WORDS.search(text)
    ]


def code_problems(code: list[str] | None, args, layout: str) -> list[str]:
    """What is wrong with spot-the-bug's code lines, marked line, and chip; they belong to spot-the-bug only."""
    mark = args.mark
    if layout != "spot-the-bug":
        given = {"--code": code, "--mark": mark, "--marker": args.marker, "--chip": args.chip}
        return [f"{name}: only for the spot-the-bug layout" for name, value in given.items() if value is not None]
    if code is None:
        return ["--code: spot-the-bug needs the file of the demo's code lines"]
    problems = []
    if args.chip and len(args.chip) > CHIP_CHARS:
        problems.append(f"--chip: at most {CHIP_CHARS} characters, such as {DEFAULT_CHIP!r}")
    if not CODE_LINES[0] <= len(code) <= CODE_LINES[1]:
        problems.append(f"--code: must be {CODE_LINES[0]} to {CODE_LINES[1]} lines, not {len(code)}")
    if long := [n for n, line in enumerate(code, 1) if len(line) > CODE_CHARS]:
        problems.append(f"--code: lines {long} are over {CODE_CHARS} characters; reflow them")
    if not (mark and 1 <= mark <= len(code)):
        problems.append(f"--mark: must be the buggy line's number, 1 to {len(code)}")
    return problems


def luminance(colour: str) -> float:
    """WCAG 2.2 relative luminance of a #RRGGBB colour."""
    channels = [int(colour.lstrip("#")[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    r, g, b = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    light, dark = sorted([luminance(a), luminance(b)], reverse=True)
    return (light + 0.05) / (dark + 0.05)


def mix(colour: str, other: str, share: float) -> str:
    """The #RRGGBB colour of share of colour over other."""
    a, b = [[int(c.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4)] for c in (colour, other)]
    return "#" + "".join(f"{round(share * x + (1 - share) * y):02X}" for x, y in zip(a, b, strict=True))


def field_of(config: dict) -> tuple[str, str]:
    """The thumbnail's field colours: channel.yaml thumbnail.field, else FIELD."""
    return tuple(config["thumbnail"].get("field", FIELD))


def _hls(colour: str) -> tuple[float, float, float]:
    return colorsys.rgb_to_hls(*[int(colour.lstrip("#")[i : i + 2], 16) / 255 for i in (0, 2, 4)])


def field_words(field: tuple[str, str]) -> str:
    """The field in words for the art prompt, such as "dark grey": FIELD_WORDS for the default field."""
    if field == FIELD:
        return FIELD_WORDS
    names = []
    for colour in field:
        hue, _, saturation = _hls(colour)
        name = "grey" if saturation < GREY_SATURATION else next(n for limit, n in HUES if hue * 360 < limit)
        names.append(name)
    lightest = max(_hls(colour)[1] for colour in field)
    grey = names == ["grey", "grey"]
    tone = ("dark" if lightest < 0.5 else "light") if grey else ("deep" if lightest < 0.6 else "light")
    return f"{tone} {names[0]}" if names[0] == names[1] else f"{tone} {names[0]}-to-{names[1]}"


def legibility(palette: dict, layout: str, field: tuple[str, str] = FIELD) -> tuple[dict, list[str]]:
    """The text, key word, and marker contrast on the field (the red marker against its warm white outline); for
    spot-the-bug, each line marker on the code panel and the marked line's text on its highlight; the least cap
    height, and what falls below the rules."""
    ratios = {
        "text": min(contrast(palette["name"], colour) for colour in field),
        "key": min(contrast(palette["suffix"], colour) for colour in field),
        "marker": contrast(palette["syntax"], palette["name"]),
    }
    least = {"text": TEXT_CONTRAST, "key": TEXT_CONTRAST, "marker": MARKER_CONTRAST}
    if layout == "spot-the-bug":
        for marker, colour in MARKER_COLOURS.items():
            ratios[marker], least[marker] = contrast(palette[colour], PANEL), MARKER_CONTRAST
        bar = mix(palette["suffix"], PANEL, HIGHLIGHT)
        ratios["line"], least["line"] = min(contrast(palette["name"], c) for c in (bar, PANEL)), TEXT_CONTRAST
    problems = [
        f"palette: {name} contrast {ratios[name]:.2f}:1 is under {least[name]}:1"
        for name in ratios
        if ratios[name] < least[name]
    ]
    report = {
        "cap_height": round(MIN_TEXT_PX * CAP_HEIGHT / 720, 3),
        "contrast": {k: round(v, 2) for k, v in ratios.items()},
    }
    return report, problems


def layout_for(number: int) -> str:
    """The default layout of video number: ROTATION in turn, so neighbouring videos differ."""
    return ROTATION[number % len(ROTATION)]


def lines(text: str, layout: str) -> list[str]:
    """The text's lines: a word a line, the last (the key word) in the accent; face-off one half a side."""
    words = text.split()
    if layout == "face-off":
        half = math.ceil(len(words) / 2)
        return [" ".join(words[:half]), " ".join(words[half:])]
    return words


def aspect(layout: str) -> str:
    return "1:1" if layout in SQUARE else "16:9"


def prompt(subject: str, config: dict, layout: str) -> str:
    """The art prompt: the channel's art style, then the subject as a scene placed for layout's text."""
    place, space = PLACES[layout]
    return (
        f"{config['thumbnail']['art_style']}. A bold, minimalist composition featuring {subject.strip().rstrip('.')}, "
        f"{place}, with a clearly readable facial expression. A strong rim light separates the subject from the "
        f"background. Bold, saturated colours. The background is a smooth, empty {field_words(field_of(config))} "
        f"gradient, leaving significant negative space toward {space} for text overlaid later. Plain, unmarked "
        f"surfaces; blank background. The purpose: art for a YouTube thumbnail that reads at small sizes. "
        f"Aspect ratio {aspect(layout)}."
    )


def request_body(text: str, ratio: str) -> dict:
    return {
        "contents": [{"parts": [{"text": text}]}],
        "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": ratio}},
    }


def image_from(response: dict) -> tuple[bytes, str]:
    """The first inline image of a generateContent response, and its media type."""
    try:
        parts = [p for c in response.get("candidates", []) for p in c["content"]["parts"] if "inlineData" in p]
        if not parts:
            raise ApiError("Gemini answered with no image")
        data = parts[0]["inlineData"]
        if data.get("mimeType") not in TYPES:
            raise ApiError(f"Gemini answered with an image of unknown type {data.get('mimeType')!r}")
        return base64.b64decode(data["data"], validate=True), data["mimeType"]
    except (KeyError, TypeError, AttributeError, binascii.Error):
        raise ApiError("Gemini answered with no image") from None


def content_box(pixels: bytes, size: int) -> tuple[int, int, int, int] | None:
    """The box (left, top, right, bottom; right and bottom exclusive) of the size x size grey pixels
    differing by more than THRESHOLD from the background, the median border pixel; None when none do."""
    rows = [pixels[y * size : (y + 1) * size] for y in range(size)]
    border = sorted([*rows[0], *rows[-1], *(row[0] for row in rows), *(row[-1] for row in rows)])
    background = border[len(border) // 2]
    found = [(x, y) for y, row in enumerate(rows) for x, value in enumerate(row) if abs(value - background) > THRESHOLD]
    if not found:
        return None
    xs, ys = [x for x, _ in found], [y for _, y in found]
    return min(xs), min(ys), max(xs) + 1, max(ys) + 1


def crop_for(box: tuple[int, int, int, int], size: tuple[int, int]) -> tuple[float, float, float]:
    """The square crop of art of size (width, height) around box: its centre x, centre y, and side, as
    shares of the art's side. It holds box with MARGIN inside the mask's opaque area as far as the art
    allows, is never under CROP, and stays on the art."""
    (left, top, right, bottom), (width, height) = box, size
    span = max((right - left) / width, (bottom - top) / height)
    side = min(1.0, max(CROP, (span + 2 * MARGIN) / (1 - 2 * FEATHER)))

    def centre(start: float, end: float) -> float:
        return min(max((start + end) / 2, side / 2), 1 - side / 2)

    return centre(left / width, right / width), centre(top / height, bottom / height), side


def page(
    layout: str,
    text: str,
    art: tuple[bytes, str] | None,
    crop: dict,
    config: dict,
    fonts_css: str,
    code: list[str] | None = None,
    mark: int | None = None,
    marker: str | None = None,
    chip: str = "",
    references=REFERENCES,
) -> str:
    """The thumbnail's HTML: the layout's template with the fonts, palette, exact text, code, chip, and art inlined."""
    template = (references / f"{layout}.html").read_text()
    spot = ["<!--{{code}}-->", "<!--{{chip}}-->", "{{marker}}"]
    needed = PLACEHOLDERS + (spot if layout == "spot-the-bug" else [])
    if missing := [p for p in needed if p not in template]:
        raise ToolError(f"references/{layout}.html lacks {', '.join(missing)}")
    colours, field = config["palette"], field_of(config)
    palette = (
        f":root {{ --bg: {colours['background']}; --red: {colours['syntax']}; --fg: {colours['name']}; "
        f"--accent: {colours['suffix']}; --field-1: {field[0]}; --field-2: {field[1]}; "
        f"--min-text: {MIN_TEXT_PX}px; --panel: {PANEL}; --bar: {mix(colours['suffix'], PANEL, HIGHLIGHT)}; "
        f"--head: {CHIP_ROW if chip else 0}px; --mark: {mark or 0}; --lines: {len(code or [])}; "
        f"--x: {crop['x']}; --y: {crop['y']}; --crop: {crop['size']}; --feather: {FEATHER * 100:g}%; }}"
    )
    image = ""
    if art:
        image = f'<div class="art"><img src="data:{art[1]};base64,{base64.b64encode(art[0]).decode()}" alt=""></div>'
    parts = {
        "/*{{fonts}}*/": fonts_css,
        "/*{{css}}*/": (references / "thumbnail.css").read_text(),
        "/*{{palette}}*/": palette,
        "/*{{js}}*/": (references / "fit.js").read_text(),
        "<!--{{art}}-->": image,
        "<!--{{text}}-->": "".join(f'<span class="line">{html.escape(line)}</span>' for line in lines(text, layout)),
        "<!--{{code}}-->": "".join(
            f'<span class="code-line marked">{indent(line)}<span class="bad">{html.escape(line.lstrip())}</span>{BUG}</span>'
            if n == mark
            else f'<span class="code-line">{html.escape(line)}</span>'
            for n, line in enumerate(code or [], 1)
        ),
        "<!--{{chip}}-->": f'<div class="chip">{SPARK}<span class="chip-text">{html.escape(chip)}</span></div>'
        if chip
        else "",
        "{{marker}}": marker or "",
    }
    for placeholder, value in parts.items():
        template = template.replace(placeholder, value)
    return template


def indent(line: str) -> str:
    """The line's leading whitespace, kept outside the marker so only the code is underlined."""
    return line[: len(line) - len(line.lstrip())]


def font_css(files: dict[str, bytes]) -> str:
    """@font-face rules embedding each font file, so the page never asks the network for a font."""
    rules = []
    for family, data in files.items():
        source = f"url(data:font/ttf;base64,{base64.b64encode(data).decode()}) format('truetype')"
        rules.append(f"@font-face {{ font-family: '{family}'; src: {source}; font-weight: 300 700; }}")
    return "\n".join(rules)


def encode(shoot, html_page: str) -> tuple[bytes, str, int | None]:
    """The first of FORMATS whose shot is under LIMIT: its bytes, format, and JPEG quality."""
    for fmt, quality in FORMATS:
        data = shoot(html_page, SIZE, fmt, quality)
        if len(data) <= LIMIT:
            return data, fmt, quality
    raise ToolError(f"the thumbnail is over YouTube's 2 MB upload limit even as JPEG at quality {FORMATS[-1][1]}")


def sheet_page(shots: list[tuple[str, bytes]]) -> tuple[str, tuple[int, int]]:
    """The contact sheet of the candidate files (name, bytes) side by side on YouTube's page colour, each at a
    large size and, below it, at 320 and 168 pixels wide; and its shot size."""
    column = (1280 - SHEET_GAP * (len(shots) + 1)) / len(shots)
    height = round(SHEET_GAP * 2 + column * 9 / 16 + 120)
    cells = []
    for name, data in shots:
        kind = "png" if name.endswith(".png") else "jpeg"
        source = f"data:image/{kind};base64,{base64.b64encode(data).decode()}"
        small = "".join(f'<img src="{source}" style="width:{width / SCALE:.2f}px" alt="">' for width in (320, 168))
        cells.append(
            f'<figure><img src="{source}" style="width:{column:.2f}px" alt=""><div>{small}</div>'
            f"<figcaption>{html.escape(name)}</figcaption></figure>"
        )
    style = (
        f"*{{margin:0}} body{{background:#0F0F0F;color:#F2EFE6;font:600 22px sans-serif;display:flex;"
        f"gap:{SHEET_GAP}px;padding:{SHEET_GAP}px}} figure div{{display:flex;gap:16px;align-items:end;margin:16px 0}}"
    )
    script = (
        "window.overflow = false; Promise.all([...document.images].map((i) => i.decode()))"
        ".then(() => { window.ready = true; }).catch(() => { window.ready = false; });"
    )
    page = f'<!doctype html><meta charset="utf-8"><style>{style}</style><body>{"".join(cells)}<script>{script}</script>'
    return page, (1280 * SCALE, height * SCALE)


# Thin shell: Gemini, Chrome, the fonts, and the video's files.

Post = Callable[[dict, str], dict]
Shoot = Callable[[str, tuple[int, int], str, int | None], bytes]
Grey = Callable[[bytes], bytes | None]


def gemini(body: dict, key: str) -> dict:
    """One generateContent call. The key goes only in the request header."""
    headers = {"Content-Type": "application/json", "x-goog-api-key": key}
    request = urllib.request.Request(GENERATE, json.dumps(body).encode(), headers)
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        try:
            message = json.loads(error.read())["error"]["message"]
        except (ValueError, KeyError, TypeError):
            message = error.reason
        raise ApiError(f"HTTP {error.code}: {message}") from None
    except (urllib.error.URLError, TimeoutError) as error:
        raise ApiError(str(getattr(error, "reason", error))) from None
    except json.JSONDecodeError:
        raise ApiError("answer is not JSON") from None


def chrome(html_page: str, size: tuple[int, int], fmt: str, quality: int | None) -> bytes:
    """The page shot in the system Chrome at size, as PNG or JPEG bytes."""
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch(channel="chrome", args=CHROME_ARGS)
        except PlaywrightError as error:
            raise ToolError(f"Chrome did not start; install Google Chrome ({str(error).splitlines()[0]})") from None
        try:
            viewport = {"width": size[0] // SCALE, "height": size[1] // SCALE}
            tab = browser.new_page(viewport=viewport, device_scale_factor=SCALE)
            tab.set_content(html_page)
            tab.wait_for_function("window.ready !== undefined")
            if tab.evaluate("window.ready") is not True:
                raise ToolError("the thumbnail's fonts did not load in Chrome; check the font files (README, Setup)")
            if tab.evaluate("window.overflow"):
                raise BadInput(
                    f"--text: does not fit the layout at the least cap height ({MIN_CAP:.0%} of the frame height); "
                    "use fewer or shorter words"
                )
            options = {"type": fmt} | ({"quality": quality} if quality else {})
            return tab.screenshot(**options)
        except PlaywrightError as error:
            raise ToolError(f"Chrome failed on the thumbnail ({str(error).splitlines()[0]})") from None
        finally:
            browser.close()


def ffmpeg_grey(art: bytes) -> bytes | None:
    """The art scaled by ffmpeg to GRID x GRID grey pixels; None when ffmpeg is missing or fails."""
    scale = f"scale={GRID}:{GRID},format=gray"
    command = ["ffmpeg", "-v", "error", "-i", "pipe:0", "-vf", scale, "-f", "rawvideo", "pipe:1"]
    try:
        done = subprocess.run(command, input=art, capture_output=True, timeout=TIMEOUT_SECONDS, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return done.stdout if done.returncode == 0 and len(done.stdout) == GRID * GRID else None


FULL = {"x": 0.5, "y": 0.5, "size": 1, "source": "full"}  # the crop of a layout showing all of the art


def subject_crop(art: bytes, grey: Grey) -> dict:
    """The crop around the art's subject, or the centred CROP view when ffmpeg fails or finds none."""
    pixels = grey(art)
    box = content_box(pixels, GRID) if pixels else None
    x, y, side = crop_for(box, (GRID, GRID)) if box else (0.5, 0.5, CROP)
    return {"x": round(x, 3), "y": round(y, 3), "size": round(side, 3), "source": "subject" if box else "centred"}


def script_title(video: Path) -> str:
    """The title of the video's script.json, which says whether the video is about AI."""
    try:
        title = json.loads((video / "script.json").read_text())["title"]
    except (FileNotFoundError, json.JSONDecodeError, KeyError, TypeError):
        title = None
    if not isinstance(title, str):
        raise BadInput(f"videos/{video.name}/script.json: missing or without a title; write-video-script writes it")
    return title


def read_code(path: Path | None) -> list[str] | None:
    if path is None:
        return None
    try:
        return path.read_text().rstrip("\n").splitlines()
    except (FileNotFoundError, UnicodeDecodeError) as error:
        raise BadInput(f"--code: cannot read {path} ({error})") from None


def read_fonts() -> dict[str, bytes]:
    folder = Path(os.environ.get(FONTS_VARIABLE) or FONTS_DIR)
    try:
        return {family: (folder / name).read_bytes() for family, name in FONTS.items()}
    except FileNotFoundError as error:
        raise ToolError(f"font {Path(error.filename).name} missing in {folder}; install it (README, Setup)") from None


def cached_art(folder: Path, wanted: str, new_art: bool) -> list[tuple[bytes, str]]:
    """The cached art images when they were made from the wanted prompt; refused when not, unless new_art."""
    try:
        record = json.loads((folder / "art.json").read_text())
        files = record.get("files") or [{"file": record["file"], "mime": record["mime"]}]  # a cache before candidates
        arts = [((folder / entry["file"]).read_bytes(), entry["mime"]) for entry in files]
    except (FileNotFoundError, json.JSONDecodeError, KeyError, TypeError, AttributeError):
        return []
    if record.get("prompt") == wanted:
        return arts
    if new_art:
        return []
    raise Refused(
        f"{folder / 'art.json'} holds art made from another prompt ({record.get('prompt')!r}); "
        "keep that subject, or pass --new-art to pay for new art"
    )


def save_art(folder: Path, wanted: str, arts: list[tuple[bytes, str]]) -> None:
    """The art images as art-1.<ext>, ... and art.json naming them and the prompt they came from."""
    folder.mkdir(exist_ok=True)
    for old in folder.glob("art*.*"):
        old.unlink()
    files = []
    for number, (art, mime) in enumerate(arts, 1):
        files.append({"file": f"art-{number}.{TYPES[mime]}", "mime": mime})
        (folder / files[-1]["file"]).write_bytes(art)
    record = {"model": MODEL, "prompt": wanted, "files": files}
    (folder / "art.json").write_text(json.dumps(record, indent=1) + "\n")


def make_art(folder: Path, wanted: str, ratio: str, arts: list, count: int, post: Post) -> list[tuple[bytes, str]]:
    """arts topped up to count images from Gemini, each saved to the cache as soon as it is paid for."""
    key = os.environ.get(KEY_VARIABLE)
    if len(arts) < count and not key:
        raise ApiError(f"{KEY_VARIABLE} is not set: put it in .env and run with uv run --env-file .env")
    arts = list(arts)
    while len(arts) < count:
        try:
            arts.append(image_from(post(request_body(wanted, ratio), key)))
        except ApiError as error:
            raise ApiError(f"Gemini: {error}") from None
        save_art(folder, wanted, arts)
    return arts


def compose(video: Path, name: str, html_page: str, shoot: Shoot) -> dict:
    """The page encoded and written as video/<name>.png or .jpg, the other format's stale file removed."""
    data, fmt, quality = encode(shoot, html_page)
    file = f"{name}.png" if fmt == "png" else f"{name}.jpg"
    (video / file).write_bytes(data)
    for stale in {f"{name}.png", f"{name}.jpg"} - {file}:
        (video / stale).unlink(missing_ok=True)
    return {"file": file, "format": fmt, "quality": quality, "bytes": len(data)}


def variants(args, layout: str) -> list[tuple[str, str | None]]:
    """Each candidate's text and marker: a value given once applies to every candidate, else one per candidate."""
    texts = args.text
    markers = args.marker or [DEFAULT_MARKER if layout == "spot-the-bug" else None]
    return [(texts[k % len(texts)], markers[k % len(markers)]) for k in range(args.candidates)]


def design(
    video: Path, args, layout: str, code: list[str] | None, config: dict, post: Post, shoot: Shoot, grey: Grey
) -> dict:
    """The video's thumbnail, or its candidates and their contact sheet, written from cached, new, or no art; the
    report of what was written."""
    checks, problems = legibility(config["palette"], layout, field_of(config))
    if problems:
        raise BadInput("\n  ".join(problems))
    fonts = font_css(read_fonts())
    count = args.candidates
    arts, wanted, new = [None] * count, None, 0
    if args.subject:
        wanted = prompt(args.subject, config, layout)
        folder = video / "thumbnail"
        cached = cached_art(folder, wanted, args.new_art)
        if new := max(0, count - len(cached)):
            print(f"Gemini: {new} new image{'s' * (new > 1)}, about USD {new * PRICE_USD:.2f}", file=sys.stderr)
        arts = make_art(folder, wanted, aspect(layout), cached, count, post)[:count]
    entries = []
    for number, (art, (text, marker)) in enumerate(zip(arts, variants(args, layout), strict=True), 1):
        crop = subject_crop(art[0], grey) if art and layout in SQUARE else FULL
        name = "thumbnail" if count == 1 else f"thumbnail-{number}"
        html_page = page(layout, text, art, crop, config, fonts, code, args.mark, marker, chip_for(args, layout))
        entries.append({"text": text, "marker": marker, "crop": crop} | compose(video, name, html_page, shoot))
    report = {
        "layout": layout,
        "about_ai": bool(AI_WORDS.search(args.title)),
        "art": "none" if not wanted else "generated" if new else "cached",
        "prompt": wanted,
        "cost_usd": round(new * PRICE_USD, 2),
        "legibility": checks,
        "width": SIZE[0],
        "height": SIZE[1],
    }
    if count == 1:
        return report | entries[0]
    sheet, size = sheet_page([(e["file"], (video / e["file"]).read_bytes()) for e in entries])
    (video / SHEET).write_bytes(shoot(sheet, size, "png", None))
    return report | {"candidates": entries, "contact_sheet": SHEET}


def chip_for(args, layout: str) -> str:
    """spot-the-bug's chip text: --chip, else DEFAULT_CHIP; empty hides it. Other layouts have none."""
    if layout != "spot-the-bug":
        return ""
    return DEFAULT_CHIP if args.chip is None else args.chip


def pick(video: Path, number: int) -> dict:
    """thumbnail.<ext> copied from candidate number's file, free; the other format's stale file removed."""
    found = [
        video / f"thumbnail-{number}.{ext}" for ext in ("png", "jpg") if (video / f"thumbnail-{number}.{ext}").is_file()
    ]
    if not found:
        raise BadInput(f"--pick: {video.name}/thumbnail-{number}.png or .jpg is missing; compose candidates first")
    data = found[0].read_bytes()
    file = f"thumbnail{found[0].suffix}"
    (video / file).write_bytes(data)
    for stale in {"thumbnail.png", "thumbnail.jpg"} - {file}:
        (video / stale).unlink(missing_ok=True)
    return {"picked": number, "file": file, "format": "png" if file.endswith("png") else "jpeg", "bytes": len(data)}


def option_problems(args) -> list[str]:
    """What is wrong with --candidates and --pick: pick stands alone, candidates need art."""
    if args.pick is not None:
        others = [
            args.text,
            args.subject,
            args.layout,
            args.code,
            args.mark,
            args.marker,
            args.chip,
            args.new_art or None,
        ]
        return ["--pick: takes no other option"] if any(o is not None for o in others) or args.candidates != 1 else []
    problems = [] if args.text is not None else ["--text: required unless --pick"]
    count, given = args.candidates, [len(v) for v in (args.text, args.marker) if v]
    if not 1 <= count <= MAX_CANDIDATES:
        problems.append(f"--candidates: must be 1 to {MAX_CANDIDATES}")
    elif any(n not in (1, count) for n in given):
        problems.append(f"--candidates: give --text and --marker once, or once for each of the {count} candidates")
    elif count > 1 and not args.subject and max(given, default=1) < count:
        problems.append(
            f"--candidates: without --subject (no paid art) candidates differ only by text or marker; "
            f"give {count} --text or {count} --marker values"
        )
    return problems


def main(
    argv: list[str] | None = None,
    post: Post = gemini,
    shoot: Shoot = chrome,
    grey: Grey = ffmpeg_grey,
    root: Path = REPO_ROOT,
) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("channel")
    parser.add_argument("number", type=int, help="the video's content issue number")
    parser.add_argument("--text", action="append", help="the challenge text; once per candidate to vary it")
    parser.add_argument("--subject")
    parser.add_argument("--layout", choices=LAYOUTS)
    parser.add_argument("--code", type=Path, help="spot-the-bug: a file of the demo's code lines")
    parser.add_argument("--mark", type=int, help="spot-the-bug: the number of the buggy line in --code")
    parser.add_argument("--marker", action="append", choices=MARKERS, help="spot-the-bug: the buggy line's marker")
    parser.add_argument("--chip", help=f"spot-the-bug: the code panel's chip, default {DEFAULT_CHIP!r}; empty hides it")
    parser.add_argument("--new-art", action="store_true", help="pay for new art when the cached art differs")
    parser.add_argument("--candidates", type=int, default=1, help="1 to 3 variants, composed as thumbnail-K")
    parser.add_argument("--pick", type=int, help="copy candidate K to thumbnail.<ext>, free")
    args = parser.parse_args(argv)
    try:
        layout = args.layout or layout_for(args.number)
        problems = option_problems(args)
        if args.pick is None and not problems:
            code = read_code(args.code)
            problems = text_problems(args.text, args.subject, layout) + code_problems(code, args, layout)
        if problems:
            raise BadInput("\n  ".join(problems))
        channel = youtube_channel.load(args.channel, root)
        video = channel.workspace / "videos" / str(args.number)
        if not video.is_dir():
            raise BadInput(f"{video.relative_to(root)}: missing; content_issue.py new creates it")
        if args.pick is not None:
            report = pick(video, args.pick)
        else:
            args.title = script_title(video)
            if problems := ai_problems(args.title, args.text, args.subject, chip_for(args, layout)):
                raise BadInput("\n  ".join(problems))
            report = design(video, args, layout, code, channel.config, post, shoot, grey)
    except (BadInput, youtube_channel.ChannelError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    except Refused as error:
        print(f"refused: {error}", file=sys.stderr)
        return 3
    except (ApiError, ToolError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
