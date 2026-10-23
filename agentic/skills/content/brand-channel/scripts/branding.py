"""Generate a channel's branding from the oneo4 logo spec (v0.4) geometry and the channel palette.

Usage: uv run agentic/skills/content/brand-channel/scripts/branding.py CHANNEL

Reads channel.yaml palette (background, syntax, name, suffix) and branding (wordmarks,
tagline, subline), and writes, in the channel workspace's branding/ folder, each asset as
an SVG source (tracked) and a PNG render (ignored by the workspace .gitignore):

  avatar          800x800    the <4/> icon on the background, inside the circle YouTube
                             crops to, with one x-height of clear space; under 15 MB
  banner          2048x1152  the first wordmark, tagline, and subline inside the centred
                             1235x338 safe area; under 6 MB
  watermark       150x150    the <4/> icon at stroke 20 on transparency; under 1 MB
  wordmark-<word> 2400 wide  <oneo4/><word> for each branding.wordmarks word, on the
                             background, height from the spec's 132-unit artboard

Geometry is the spec's, unaltered: glyph paths, 68-unit advance, suffix from x = 500 at
0.6 times the tag weight of 14, icon viewBox 2 -18 200 200 at stroke 16, round caps and
joins, stroke only. Layer order: name strokes, then suffix strokes, then syntax strokes
on top, so the shared 4/ stroke stays unbroken. A wordmark letter the spec has no glyph
for (GLYPHS) is refused, and so is a banner line wider than the safe area at CHAR_EM.

Render: the system Chrome, through Playwright, shoots each SVG at its size as PNG with
the Space Grotesk and Fira Code files embedded (RENDER_FONTS, else .cache/fonts in the
home folder; nothing loads from the network). Every render is checked for its size and
YouTube's file limit before any file is written. Prints a JSON report of each asset:
name, svg, png, width, height, bytes, limit.

Exit codes: 0 written, 1 a Chrome, font, or file error, or a render of the wrong size or
over its limit, 2 bad input (an invalid channel, a letter without a glyph, a line too wide).
"""

import argparse
import base64
import html
import json
import os
import struct
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO_ROOT / "agentic" / "scripts"))
import youtube_channel

# Logo spec v0.4 geometry, in SVG units. The tag <oneo4/>: name strokes, then syntax strokes.
NAME = (
    '<g transform="translate(68,0)"><ellipse cx="32" cy="90" rx="22" ry="30"/></g>'
    '<g transform="translate(136,0)"><path d="M12 120 V60 M12 86 C12 70 22 60 34 60 C47 60 54 69 54 84 V120"/></g>'
    '<g transform="translate(204,0)"><path d="M11 92 H54 C54 72 45 60 32 60 C18 60 10 73 10 90 C10 108 19 120 34 120 '
    'C44 120 50 116 54 110"/></g>'
    '<g transform="translate(272,0)"><ellipse cx="32" cy="90" rx="22" ry="30"/></g>'
)
FOUR_ARM = '<g transform="translate({x},0)"><path d="M58 34 L4 104 H66"/></g>'
SYNTAX = (
    '<path d="M50 56 L12 90 L50 124"/>'
    '<g transform="translate({four},0)"><path d="M60 28 L22 136"/></g>'
    '<g transform="translate({close},0)"><path d="M14 56 L52 90 L14 124"/></g>'
)
GLYPHS = {  # the suffix glyphs the spec draws (tech, ark, testlab)
    "a": '<ellipse cx="31" cy="90" rx="21" ry="30"/><path d="M52 60 V120"/>',
    "b": '<path d="M12 36 V120"/><ellipse cx="33" cy="90" rx="21" ry="30"/>',
    "c": '<path d="M54 70 C49 63 42 60 33 60 C19 60 10 73 10 90 C10 107 19 120 33 120 C42 120 49 117 54 110"/>',
    "e": '<path d="M11 92 H54 C54 72 45 60 32 60 C18 60 10 73 10 90 C10 108 19 120 34 120 C44 120 50 116 54 110"/>',
    "h": '<path d="M12 36 V120 M12 86 C12 70 22 60 34 60 C47 60 54 69 54 84 V120"/>',
    "k": '<path d="M12 36 V120 M52 62 L12 98 M27 85 L54 120"/>',
    "l": '<path d="M12 36 H28 V106 C28 115 33 120 42 120 H52"/>',
    "r": '<path d="M12 120 V60 M12 84 C12 70 22 60 36 60 C44 60 50 62 54 66"/>',
    "s": '<path d="M52 68 C48 62 41 60 32 60 C20 60 12 66 12 75 C12 84 20 87 32 90 C44 93 52 96 52 105 C52 114 44 120 '
    '32 120 C22 120 14 117 10 110"/>',
    "t": '<path d="M28 36 V106 C28 115 33 120 42 120 H54 M10 62 H52"/>',
}
TAG_WEIGHT = 14
SUFFIX_WEIGHT = round(0.6 * TAG_WEIGHT, 2)  # 8.4
SUFFIX_X, ADVANCE = 500, 68
ARTBOARD = (-10, 16, 132)  # wordmark viewBox x, y, and height; width 68 per glyph + 514 (testlab: 990)
INK = (21, 143)  # the tag's top and bottom, the 4/ stroke with its round caps
X_HEIGHT = 60  # the clear space around the logo
ICON_BOX = "2 -18 200 200"
ICON_WEIGHT, WATERMARK_WEIGHT = 16, 20  # the spec suggests 18-20 where the icon shows small
ICON_CENTRE, ICON_REACH = (102, 82), 99  # the icon's centre and the farthest its ink reaches from it
FONTS = {"Space Grotesk": "SpaceGrotesk.ttf", "Fira Code": "FiraCode.ttf"}
FONTS_VARIABLE = "RENDER_FONTS"  # the same fonts render-video and design-thumbnail use
FONTS_DIR = Path.home() / ".cache" / "fonts"

# YouTube's sizes and limits (Help 10456525).
AVATAR, WATERMARK, BANNER, SAFE = (800, 800), (150, 150), (2048, 1152), (1235, 338)
WORDMARK_WIDTH = 2400
LIMITS = {"avatar": 15_000_000, "banner": 6_000_000, "watermark": 1_000_000}  # bytes, kept under
# Banner layout, in pixels: the wordmark at most this scale, then clear space, then the two lines.
WORDMARK_SCALE = 1.1
TAGLINE, SUBLINE = ("Space Grotesk", "sans-serif", 46), ("Fira Code", "monospace", 30)
LINE_GAP = 24
ASCENT, DESCENT = 0.75, 0.25  # of the font size, above and below the baseline
CHAR_EM = 0.62  # widest average character advance of the two fonts, of the font size


class BadInput(Exception):
    """A letter without a glyph or a line too wide for the safe area: exit 2."""


class ToolError(Exception):
    """Chrome or a font failing, or a render of the wrong size or over its limit: exit 1."""


@dataclass
class Asset:
    name: str
    svg: str
    size: tuple[int, int]
    limit: int | None


def num(value: float) -> str:
    return f"{round(value, 1):g}"


def missing_glyphs(word: str) -> list[str]:
    return sorted({letter for letter in word if letter not in GLYPHS})


def artboard_width(word: str) -> int:
    return ADVANCE * len(word) + 514


def wordmark(palette: dict, word: str) -> str:
    """<oneo4/><word> per spec sections 3 and 8: name, then suffix, then syntax strokes."""
    suffix = "".join(
        f'<g transform="translate({SUFFIX_X + ADVANCE * i},0)">{GLYPHS[c]}</g>' for i, c in enumerate(word)
    )
    return (
        '<g fill="none" stroke-linecap="round" stroke-linejoin="round">'
        f'<g stroke="{palette["name"]}" stroke-width="{TAG_WEIGHT}">{NAME}{FOUR_ARM.format(x=340)}</g>'
        f'<g stroke="{palette["suffix"]}" stroke-width="{num(SUFFIX_WEIGHT)}">{suffix}</g>'
        f'<g stroke="{palette["syntax"]}" stroke-width="{TAG_WEIGHT}">{SYNTAX.format(four=340, close=416)}</g></g>'
    )


def icon(palette: dict, weight: int) -> str:
    """<4/> per spec section 5: the 4's arm, then the syntax strokes."""
    return (
        f'<g fill="none" stroke-linecap="round" stroke-linejoin="round" stroke-width="{weight}">'
        f'<g stroke="{palette["name"]}">{FOUR_ARM.format(x=64)}</g>'
        f'<g stroke="{palette["syntax"]}">{SYNTAX.format(four=64, close=140)}</g></g>'
    )


def svg(size: tuple[int, int], view: str, body: str, background: str | None) -> str:
    style = f' style="background:{background}"' if background else ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size[0]}" height="{size[1]}" viewBox="{view}"{style}>'
        f"{body}</svg>"
    )


def avatar(palette: dict) -> str:
    """The icon centred in the circle YouTube crops the picture to, one x-height clear of its edge."""
    side = 2 * (ICON_REACH + X_HEIGHT)
    x, y = ICON_CENTRE[0] - side / 2, ICON_CENTRE[1] - side / 2
    return svg(AVATAR, f"{num(x)} {num(y)} {side} {side}", icon(palette, ICON_WEIGHT), palette["background"])


def line_problems(branding: dict) -> list[str]:
    problems = []
    for field, (_, _, size) in (("tagline", TAGLINE), ("subline", SUBLINE)):
        widest = int(SAFE[0] / (CHAR_EM * size))
        if len(branding[field]) > widest:
            problems.append(f"branding.{field}: at most {widest} characters to fit the banner's safe area")
    return problems


def banner(palette: dict, branding: dict) -> str:
    """The first wordmark and the two lines, stacked and centred in the safe area."""
    word = branding["wordmarks"][0]
    width = artboard_width(word)
    scale = min(WORDMARK_SCALE, SAFE[0] / width)
    stack = (INK[1] - INK[0] + X_HEIGHT) * scale + TAGLINE[2] + LINE_GAP + SUBLINE[2]
    top = (BANNER[1] - SAFE[1]) / 2 + (SAFE[1] - stack) / 2
    logo_y = top - (INK[0] - ARTBOARD[1]) * scale
    tag_y = top + (INK[1] - INK[0] + X_HEIGHT) * scale + ASCENT * TAGLINE[2]
    sub_y = tag_y + DESCENT * TAGLINE[2] + LINE_GAP + ASCENT * SUBLINE[2]
    centre = BANNER[0] // 2
    logo = (
        f'<svg x="{num(centre - width * scale / 2)}" y="{num(logo_y)}" width="{num(width * scale)}" '
        f'height="{num(ARTBOARD[2] * scale)}" viewBox="{ARTBOARD[0]} {ARTBOARD[1]} {width} {ARTBOARD[2]}">'
        f"{wordmark(palette, word)}</svg>"
    )
    lines = ""
    for (family, generic, size), y, text, colour in (
        (TAGLINE, tag_y, branding["tagline"], palette["name"]),
        (SUBLINE, sub_y, branding["subline"], palette["suffix"]),  # never syntax red: too low in contrast for text
    ):
        lines += (
            f'<text x="{centre}" y="{num(y)}" text-anchor="middle" font-family="\'{family}\', {generic}" '
            f'font-size="{size}" fill="{colour}">{html.escape(text, quote=False)}</text>'
        )
    return svg(BANNER, f"0 0 {BANNER[0]} {BANNER[1]}", logo + lines, palette["background"])


def assets(config: dict) -> list[Asset]:
    """Every branding asset of the channel, built from the spec geometry and the channel palette."""
    palette, branding = config["palette"], config["branding"]
    problems = [
        f"branding.wordmarks: {word!r} has no glyph in the logo spec for "
        f"{', '.join(repr(c) for c in missing)} (glyphs: {' '.join(GLYPHS)})"
        for word in branding["wordmarks"]
        if (missing := missing_glyphs(word))
    ] + line_problems(branding)
    if problems:
        raise BadInput("\n  ".join(problems))
    built = [
        Asset("avatar", avatar(palette), AVATAR, LIMITS["avatar"]),
        Asset("banner", banner(palette, branding), BANNER, LIMITS["banner"]),
        Asset(
            "watermark", svg(WATERMARK, ICON_BOX, icon(palette, WATERMARK_WEIGHT), None), WATERMARK, LIMITS["watermark"]
        ),
    ]
    for word in branding["wordmarks"]:
        width = artboard_width(word)
        size = (WORDMARK_WIDTH, round(WORDMARK_WIDTH * ARTBOARD[2] / width))
        view = f"{ARTBOARD[0]} {ARTBOARD[1]} {width} {ARTBOARD[2]}"
        built.append(
            Asset(f"wordmark-{word}", svg(size, view, wordmark(palette, word), palette["background"]), size, None)
        )
    return built


def png_size(data: bytes) -> tuple[int, int] | None:
    if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        return None
    return struct.unpack(">II", data[16:24])


def checked(asset: Asset, data: bytes) -> bytes:
    """The render, refused when it is not at the asset's size or not under its limit."""
    if (got := png_size(data)) != asset.size:
        shown = f"{got[0]}x{got[1]}" if got else "not a PNG"
        raise ToolError(f"{asset.name}.png rendered {shown}, expected {asset.size[0]}x{asset.size[1]}")
    if asset.limit and len(data) >= asset.limit:
        raise ToolError(f"{asset.name}.png is {len(data)} bytes, not under YouTube's limit of {asset.limit}")
    return data


# Thin shell: Chrome, the fonts, and the workspace's branding folder.

Shoot = Callable[[str, tuple[int, int]], bytes]


def font_css() -> str:
    """@font-face rules embedding each font file, so the page never asks the network for a font."""
    folder = Path(os.environ.get(FONTS_VARIABLE) or FONTS_DIR)
    rules = []
    for family, name in FONTS.items():
        try:
            data = (folder / name).read_bytes()
        except FileNotFoundError:
            raise ToolError(f"font {name} missing in {folder}; install it (README, Setup)") from None
        source = f"url(data:font/ttf;base64,{base64.b64encode(data).decode()}) format('truetype')"
        rules.append(f"@font-face {{ font-family: '{family}'; src: {source}; font-weight: 300 700; }}")
    return "\n".join(rules)


def page(svg_text: str, fonts: str) -> str:
    return (
        f"<!doctype html><meta charset=utf-8><style>{fonts}\n*{{margin:0}}html,body{{background:transparent}}"
        f"svg{{display:block}}</style>{svg_text}"
    )


FONTS_LOADED = "Promise.all([...document.fonts].map(f => f.load())).then(fs => fs.every(f => f.status === 'loaded'))"


def chrome(svg_text: str, size: tuple[int, int]) -> bytes:
    """The SVG shot in the system Chrome at size, as PNG bytes, transparent where it has no background."""
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import sync_playwright

    fonts = font_css()
    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch(channel="chrome", args=["--force-color-profile=srgb"])
        except PlaywrightError as error:
            raise ToolError(f"Chrome did not start; install Google Chrome ({str(error).splitlines()[0]})") from None
        try:
            tab = browser.new_page(viewport={"width": size[0], "height": size[1]})
            tab.set_content(page(svg_text, fonts))
            if tab.evaluate(FONTS_LOADED) is not True:
                raise ToolError("the branding fonts did not load in Chrome; check the font files (README, Setup)")
            return tab.screenshot(type="png", omit_background=True)
        except PlaywrightError as error:
            raise ToolError(f"Chrome failed on the branding ({str(error).splitlines()[0]})") from None
        finally:
            browser.close()


def main(argv: list[str] | None = None, root: Path = REPO_ROOT, shoot: Shoot = chrome) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("channel")
    args = parser.parse_args(argv)
    try:
        channel = youtube_channel.load(args.channel, root)
        built = assets(channel.config)
        renders = [checked(asset, shoot(asset.svg, asset.size)) for asset in built]
        folder = channel.workspace / "branding"
        folder.mkdir(exist_ok=True)
        report = []
        for asset, data in zip(built, renders, strict=True):
            (folder / f"{asset.name}.svg").write_text(asset.svg + "\n")
            (folder / f"{asset.name}.png").write_bytes(data)
            report.append(
                {
                    "name": asset.name,
                    "svg": f"branding/{asset.name}.svg",
                    "png": f"branding/{asset.name}.png",
                    "width": asset.size[0],
                    "height": asset.size[1],
                    "bytes": len(data),
                    "limit": asset.limit,
                }
            )
    except (BadInput, youtube_channel.ChannelError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    except (ToolError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(json.dumps({"assets": report}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
