"""PROTOTYPE: channel branding generated from the oneo4 logo spec (v0.4) geometry, in three palettes.

uv run --no-project steps/branding.py -> out/branding/<palette>-{avatar,banner,banner-guides,watermark,testlab,aksa}.png
YouTube (Help 10456525): picture renders at 98x98, banner min 2048x1152 with a 1235x338 safe area, watermark 150x150.
"""

import subprocess
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "out" / "branding"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PALETTES = {  # owner's pick 2026-10-23: deep red syntax, warm white name, cyan suffix, black background
    "chosen": {"bg": "#000000", "syntax": "#CC0000", "name": "#F2EFE6", "suffix": "#00E5FF", "accent": "#00E5FF"},
}
NAME = """<g transform="translate(68,0)"><ellipse cx="32" cy="90" rx="22" ry="30"/></g>
<g transform="translate(136,0)"><path d="M12 120 V60 M12 86 C12 70 22 60 34 60 C47 60 54 69 54 84 V120"/></g>
<g transform="translate(204,0)"><path d="M11 92 H54 C54 72 45 60 32 60 C18 60 10 73 10 90 C10 108 19 120 34 120 C44 120 50 116 54 110"/></g>
<g transform="translate(272,0)"><ellipse cx="32" cy="90" rx="22" ry="30"/></g>"""
FOUR_ARM = '<g transform="translate({x},0)"><path d="M58 34 L4 104 H66"/></g>'
SYNTAX = """<path d="M50 56 L12 90 L50 124"/><g transform="translate({four},0)"><path d="M60 28 L22 136"/></g>
<g transform="translate({close},0)"><path d="M14 56 L52 90 L14 124"/></g>"""
GLYPHS = {
    "t": '<path d="M28 36 V106 C28 115 33 120 42 120 H54 M10 62 H52"/>',
    "e": '<path d="M11 92 H54 C54 72 45 60 32 60 C18 60 10 73 10 90 C10 108 19 120 34 120 C44 120 50 116 54 110"/>',
    "s": '<path d="M52 68 C48 62 41 60 32 60 C20 60 12 66 12 75 C12 84 20 87 32 90 C44 93 52 96 52 105 C52 114 44 120 32 '
    '120 C22 120 14 117 10 110"/>',
    "l": '<path d="M12 36 H28 V106 C28 115 33 120 42 120 H52"/>',
    "a": '<ellipse cx="31" cy="90" rx="21" ry="30"/><path d="M52 60 V120"/>',
    "b": '<path d="M12 36 V120"/><ellipse cx="33" cy="90" rx="21" ry="30"/>',
    "k": '<path d="M12 36 V120 M52 62 L12 98 M27 85 L54 120"/>',
}


def wordmark(p: dict, suffix: str) -> tuple[str, int]:
    """Inner SVG of <oneo4/>suffix and its viewBox width, per spec section 3 and 8."""
    suf = "".join(f'<g transform="translate({500 + 68 * i},0)">{GLYPHS[c]}</g>' for i, c in enumerate(suffix))
    width = 500 + 68 * len(suffix) + 10
    body = (
        f'<g fill="none" stroke-linecap="round" stroke-linejoin="round">'
        f'<g stroke="{p["name"]}" stroke-width="14">{NAME}{FOUR_ARM.format(x=340)}</g>'
        f'<g stroke="{p["suffix"]}" stroke-width="8.4">{suf}</g>'
        f'<g stroke="{p["syntax"]}" stroke-width="14">{SYNTAX.format(four=340, close=416)}</g></g>'
    )
    return body, width


def icon(p: dict, stroke: int = 16) -> str:
    return (
        f'<g fill="none" stroke-linecap="round" stroke-linejoin="round" stroke-width="{stroke}">'
        f'<g stroke="{p["name"]}">{FOUR_ARM.format(x=64)}</g>'
        f'<g stroke="{p["syntax"]}">{SYNTAX.format(four=64, close=140)}</g></g>'
    )


def page(w: int, h: int, bg: str, svg: str, extra: str = "") -> str:
    return (
        f'<!doctype html><meta charset=utf-8><link rel=stylesheet href="../fonts/fonts.css"><style>*{{margin:0}}'
        f"body{{width:{w}px;height:{h}px;background:{bg};overflow:hidden;position:relative}}{extra}</style>"
        f"<body>{svg}</body>"
    )


def shoot(html: str, w: int, h: int, png: Path) -> None:
    src = png.with_suffix(".html")
    src.write_text(html)
    subprocess.run(
        [
            CHROME,
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            f"--window-size={w},{h}",
            "--virtual-time-budget=1500",
            f"--screenshot={png}",
            src.as_uri(),
        ],
        check=True,
        capture_output=True,
    )


def banner(p: dict, guides: bool) -> str:
    body, width = wordmark(p, "testlab")
    logo = f'<svg x="406" y="420" width="1236" height="166" viewBox="-10 16 {width} 132">{body}</svg>'
    tag = (
        f'<text x="1024" y="680" text-anchor="middle" font-family="Space Grotesk" font-size="46" '
        f'fill="{p["name"]}">How testers think when AI writes the code</text>'
        f'<text x="1024" y="740" text-anchor="middle" font-family="Fira Code" font-size="30" fill="{p["accent"]}">'
        f"spot the bug · test the AI · weekly</text>"
    )
    grid = (
        f'<defs><pattern id="g" width="64" height="64" patternUnits="userSpaceOnUse"><path d="M64 0H0V64" '
        f'fill="none" stroke="{p["name"]}" stroke-opacity=".05"/></pattern></defs>'
        f'<rect width="2048" height="1152" fill="url(#g)"/>'
    )
    guide = (
        (
            '<rect x="406.5" y="407" width="1235" height="338" fill="none" stroke="#ffe066" stroke-width="4" '
            'stroke-dasharray="16 10"/><text x="420" y="400" font-size="28" fill="#ffe066" font-family="Fira Code">'
            "safe area 1235x338 (all devices)</text>"
        )
        if guides
        else ""
    )
    return f'<svg width="2048" height="1152" viewBox="0 0 2048 1152">{grid}{logo}{tag}{guide}</svg>'


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, p in PALETTES.items():
        shoot(
            page(800, 800, p["bg"], f'<svg width="800" height="800" viewBox="2 -18 200 200">{icon(p)}</svg>'),
            800,
            800,
            OUT / f"{name}-avatar.png",
        )
        shoot(
            page(150, 150, "transparent", f'<svg width="150" height="150" viewBox="2 -18 200 200">{icon(p, 20)}</svg>'),
            150,
            150,
            OUT / f"{name}-watermark.png",
        )
        shoot(page(2048, 1152, p["bg"], banner(p, False)), 2048, 1152, OUT / f"{name}-banner.png")
        shoot(page(2048, 1152, p["bg"], banner(p, True)), 2048, 1152, OUT / f"{name}-banner-guides.png")
        for suffix in ("testlab", "aksa"):
            body, width = wordmark(p, suffix)
            h = round(1200 * 132 / (width + 10)) * 2
            shoot(
                page(2400, h, p["bg"], f'<svg width="2400" height="{h}" viewBox="-10 16 {width} 132">{body}</svg>'),
                2400,
                h,
                OUT / f"{name}-{suffix}.png",
            )


if __name__ == "__main__" and "combos" not in __import__("sys").argv:
    main()


SYNTAX_COLORS = {
    "signal red": "#FF0000",
    "deep red": "#CC0000",
    "orange-red": "#FF3D00",
    "amber": "#FFB000",
    "magenta": "#FF2E88",
    "cyan": "#00E5FF",
    "green": "#3FFF8A",
}
NAME_COLORS = {"white": "#FFFFFF", "silver": "#C9CED6", "warm white": "#F2EFE6", "cyan": "#00E5FF", "amber": "#FFB000"}


def combos(suffix_color: str = "#00e5ff") -> None:
    """Grid of syntax (< / >) x name (oneo4) colours on black, suffix fixed. -> out/branding/combos.png"""
    cells = []
    for sname, s in SYNTAX_COLORS.items():
        for nname, n in NAME_COLORS.items():
            if s.lower() == n.lower():
                continue
            p = {"syntax": s, "name": n, "suffix": suffix_color}
            body, width = wordmark(p, "testlab")
            cells.append(
                f'<div class="c"><svg viewBox="-10 16 {width} 132">{body}</svg>'
                f'<svg class="i" viewBox="2 -18 200 200">{icon(p)}</svg>'
                f"<p>&lt;/&gt; {sname} {s} &middot; oneo4 {nname} {n}</p></div>"
            )
    css = (
        ".g{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;padding:24px}"
        ".c{border:1px solid #222;border-radius:10px;padding:14px;display:grid;grid-template-columns:1fr 90px;gap:10px;"
        "align-items:center}.c svg{width:100%}.c p{grid-column:1/3;color:#888;font:15px 'Fira Code',monospace;margin:0}"
    )
    rows = (len(cells) + 2) // 3
    h = 40 + rows * 205
    shoot(page(2400, h, "#000000", f'<div class="g">{"".join(cells)}</div>', css), 2400, h, OUT / "combos.png")


if __name__ == "__main__" and "combos" in __import__("sys").argv:
    combos()
