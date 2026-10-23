"""Design a video's thumbnail: a channel layout holding the exact text, around text-free Gemini art.

Usage: uv run --env-file .env agentic/skills/content/design-thumbnail/scripts/thumbnail.py
         CHANNEL N --text "..." --subject "..." [--layout L] [--new-art]

  --text      the thumbnail text, one to MAX_WORDS words on one line, shown exactly as given
  --subject   what the art shows, in words; the prompt adds the style and forbids any text
  --layout    split, code-circle, or face-off; default LAYOUTS[N % 3], so layouts rotate
  --new-art   pay for new art when the cached art was made from another prompt

Reads channel.yaml palette and thumbnail.art_style, and writes, in the channel workspace's
videos/<N>/ (which must exist):

  thumbnail/art.<ext>, art.json   the art and the prompt it was made from: the cache
  thumbnail.png or thumbnail.jpg  the thumbnail, SIZE pixels, under LIMIT bytes

Art: one Gemini generateContent request (MODEL, responseModalities IMAGE, aspect ratio
1:1) with the prompt "<art_style>: <subject>. Absolutely no text, letters, or numbers. ...
Solid flat background colour <palette.background>, centred subject with margin". It costs
about USD 0.07 an image (no free tier). The key is the GEMINI_API_KEY environment variable,
read from .env by uv run --env-file .env; it is never printed. Art made from the same prompt
is reused without a call, so re-composing never pays twice; a different prompt is refused
(exit 3) unless --new-art.

Compose: references/<layout>.html with references/thumbnail.css and references/fit.js, the
palette as CSS variables, the text HTML-escaped into its lines (split: two lines, code-circle:
one, face-off: one word a line), the art embedded and centre-cropped to CROP of its side, and
the Space Grotesk and Fira Code files embedded (RENDER_FONTS, else .cache/fonts in the home
folder; nothing loads from the network). fit.js shrinks the text until it fits its box.

Encode: the system Chrome, through Playwright, shoots the 1280x720 page at 3x for SIZE, as
PNG, else JPEG at falling quality (CANDIDATES), the first under LIMIT (YouTube's 2 MB upload
limit); the other format's stale file is removed. Prints a JSON report: layout, text, art
(cached or generated), prompt, file, format, quality, bytes, width, height.

Needs Google Chrome and the fonts (README, Setup); GEMINI_API_KEY only when art is generated.

Exit codes: 0 written, 1 a Gemini, Chrome, font, or file error, the key missing, or no format
under LIMIT, 2 bad input (an invalid channel, text, or subject, or no video folder), 3 refused
(cached art from another prompt without --new-art).
"""

import argparse
import base64
import binascii
import html
import json
import math
import os
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
LAYOUTS = ["split", "code-circle", "face-off"]
MAX_WORDS = 4
SIZE = (3840, 2160)  # YouTube's recommended thumbnail size, 16:9
SCALE = 3  # the templates are a 1280x720 canvas
LIMIT = 2_000_000  # YouTube's 2 MB thumbnail upload limit
CANDIDATES = [("png", None), ("jpeg", 92), ("jpeg", 85), ("jpeg", 75), ("jpeg", 65)]
CROP = 0.62  # share of the art's side kept, centred, as the prototype
NO_TEXT = "Absolutely no text, letters, or numbers, and no logos, signs, labels, or symbols with writing."
TYPES = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}
CHROME_ARGS = ["--disable-gpu", "--force-color-profile=srgb"]
FONTS = {"Space Grotesk": "SpaceGrotesk.ttf", "Fira Code": "FiraCode.ttf"}
FONTS_VARIABLE = "RENDER_FONTS"  # the same fonts render-video uses
FONTS_DIR = Path.home() / ".cache" / "fonts"
PLACEHOLDERS = ["/*{{fonts}}*/", "/*{{css}}*/", "/*{{palette}}*/", "/*{{js}}*/", "{{art}}", "<!--{{text}}-->"]


class BadInput(Exception):
    """Invalid text or subject, or no video folder: exit 2."""


class Refused(Exception):
    """Cached art from another prompt without --new-art: exit 3."""


class ApiError(Exception):
    """Gemini failed or answered without an image, or the key is missing: exit 1. Never holds the key."""


class ToolError(Exception):
    """Chrome, a font, or a template missing or failing, or no format under LIMIT: exit 1."""


def text_problems(text: str, subject: str) -> list[str]:
    problems = []
    words = text.split()
    if "\n" in text or not 1 <= len(words) <= MAX_WORDS:
        problems.append(f"--text: must be 1 to {MAX_WORDS} words on one line")
    if not subject.strip():
        problems.append("--subject: must say what the art shows")
    return problems


def layout_for(number: int) -> str:
    """The layout of video number: the layouts in turn, so neighbouring videos differ."""
    return LAYOUTS[number % len(LAYOUTS)]


def lines(text: str, layout: str) -> list[str]:
    """The text's lines in layout: split two (the longer first), code-circle one, face-off a word each."""
    words = text.split()
    if layout == "face-off":
        return words
    if layout == "split" and len(words) > 1:
        half = math.ceil(len(words) / 2)
        return [" ".join(words[:half]), " ".join(words[half:])]
    return [" ".join(words)]


def prompt(subject: str, config: dict) -> str:
    """The art prompt: the channel's art style, the subject, never any text, on the channel background."""
    background = config["palette"]["background"]
    return (
        f"{config['thumbnail']['art_style']}: {subject.strip().rstrip('.')}. {NO_TEXT} "
        f"Solid flat background colour {background}, centred subject with generous margin around it."
    )


def request_body(text: str) -> dict:
    return {
        "contents": [{"parts": [{"text": text}]}],
        "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": "1:1"}},
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


def page(layout: str, text: str, art: bytes, mime: str, config: dict, fonts_css: str, references=REFERENCES) -> str:
    """The thumbnail's HTML: the layout's template with the fonts, palette, exact text, and art inlined."""
    template = (references / f"{layout}.html").read_text()
    if missing := [p for p in PLACEHOLDERS if p not in template]:
        raise ToolError(f"references/{layout}.html lacks {', '.join(missing)}")
    colours = config["palette"]
    palette = (
        f":root {{ --bg: {colours['background']}; --red: {colours['syntax']}; --fg: {colours['name']}; "
        f"--accent: {colours['suffix']}; --crop: {CROP}; }}"
    )
    parts = {
        "/*{{fonts}}*/": fonts_css,
        "/*{{css}}*/": (references / "thumbnail.css").read_text(),
        "/*{{palette}}*/": palette,
        "/*{{js}}*/": (references / "fit.js").read_text(),
        "{{art}}": f"data:{mime};base64,{base64.b64encode(art).decode()}",
        "<!--{{text}}-->": "".join(f'<span class="line">{html.escape(line)}</span>' for line in lines(text, layout)),
    }
    for placeholder, value in parts.items():
        template = template.replace(placeholder, value)
    return template


def font_css(files: dict[str, bytes]) -> str:
    """@font-face rules embedding each font file, so the page never asks the network for a font."""
    rules = []
    for family, data in files.items():
        source = f"url(data:font/ttf;base64,{base64.b64encode(data).decode()}) format('truetype')"
        rules.append(f"@font-face {{ font-family: '{family}'; src: {source}; font-weight: 300 700; }}")
    return "\n".join(rules)


def encode(shoot, html_page: str) -> tuple[bytes, str, int | None]:
    """The first of CANDIDATES whose shot is under LIMIT: its bytes, format, and JPEG quality."""
    for fmt, quality in CANDIDATES:
        data = shoot(html_page, SIZE, fmt, quality)
        if len(data) <= LIMIT:
            return data, fmt, quality
    raise ToolError(f"the thumbnail is over YouTube's 2 MB upload limit even as JPEG at quality {CANDIDATES[-1][1]}")


# Thin shell: Gemini, Chrome, the fonts, and the video's files.

Post = Callable[[dict, str], dict]
Shoot = Callable[[str, tuple[int, int], str, int | None], bytes]


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
            options = {"type": fmt} | ({"quality": quality} if quality else {})
            return tab.screenshot(**options)
        except PlaywrightError as error:
            raise ToolError(f"Chrome failed on the thumbnail ({str(error).splitlines()[0]})") from None
        finally:
            browser.close()


def read_fonts() -> dict[str, bytes]:
    folder = Path(os.environ.get(FONTS_VARIABLE) or FONTS_DIR)
    try:
        return {family: (folder / name).read_bytes() for family, name in FONTS.items()}
    except FileNotFoundError as error:
        raise ToolError(f"font {Path(error.filename).name} missing in {folder}; install it (README, Setup)") from None


def cached_art(folder: Path, wanted: str, new_art: bool) -> tuple[bytes, str] | None:
    """The cached art when it was made from the wanted prompt; refused when it was not, unless new_art."""
    try:
        record = json.loads((folder / "art.json").read_text())
        art = (folder / record["file"]).read_bytes()
    except (FileNotFoundError, json.JSONDecodeError, KeyError, TypeError):
        return None
    if record.get("prompt") == wanted:
        return art, record["mime"]
    if new_art:
        return None
    raise Refused(
        f"{folder / 'art.json'} holds art made from another prompt ({record.get('prompt')!r}); "
        "keep that subject, or pass --new-art to pay for new art"
    )


def make_art(folder: Path, wanted: str, post: Post) -> tuple[bytes, str]:
    """New art from Gemini, written to the cache with the prompt it came from."""
    key = os.environ.get(KEY_VARIABLE)
    if not key:
        raise ApiError(f"{KEY_VARIABLE} is not set: put it in .env and run with uv run --env-file .env")
    try:
        art, mime = image_from(post(request_body(wanted), key))
    except ApiError as error:
        raise ApiError(f"Gemini: {error}") from None
    folder.mkdir(exist_ok=True)
    for old in folder.glob("art.*"):
        old.unlink()
    file = f"art.{TYPES[mime]}"
    (folder / file).write_bytes(art)
    record = {"model": MODEL, "prompt": wanted, "file": file, "mime": mime}
    (folder / "art.json").write_text(json.dumps(record, indent=1) + "\n")
    return art, mime


def design(video: Path, args, config: dict, post: Post, shoot: Shoot) -> dict:
    """The video's thumbnail written from the cached or new art; the report of what was written."""
    layout = args.layout or layout_for(args.number)
    fonts = font_css(read_fonts())
    wanted = prompt(args.subject, config)
    folder = video / "thumbnail"
    cached = cached_art(folder, wanted, args.new_art)
    art, mime = cached or make_art(folder, wanted, post)
    data, fmt, quality = encode(shoot, page(layout, args.text, art, mime, config, fonts))
    name = "thumbnail.png" if fmt == "png" else "thumbnail.jpg"
    (video / name).write_bytes(data)
    for stale in {"thumbnail.png", "thumbnail.jpg"} - {name}:
        (video / stale).unlink(missing_ok=True)
    return {
        "layout": layout,
        "text": args.text,
        "art": "cached" if cached else "generated",
        "prompt": wanted,
        "file": name,
        "format": fmt,
        "quality": quality,
        "bytes": len(data),
        "width": SIZE[0],
        "height": SIZE[1],
    }


def main(argv: list[str] | None = None, post: Post = gemini, shoot: Shoot = chrome, root: Path = REPO_ROOT) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("channel")
    parser.add_argument("number", type=int, help="the video's content issue number")
    parser.add_argument("--text", required=True)
    parser.add_argument("--subject", required=True)
    parser.add_argument("--layout", choices=LAYOUTS)
    parser.add_argument("--new-art", action="store_true", help="pay for new art when the cached art differs")
    args = parser.parse_args(argv)
    try:
        if problems := text_problems(args.text, args.subject):
            raise BadInput("\n  ".join(problems))
        channel = youtube_channel.load(args.channel, root)
        video = channel.workspace / "videos" / str(args.number)
        if not video.is_dir():
            raise BadInput(f"{video.relative_to(root)}: missing; content_issue.py new creates it")
        report = design(video, args, channel.config, post, shoot)
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
