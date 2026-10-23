"""PROTOTYPE: combined thumbnails, Claude-designed SVG layouts around Gemini art. -> out/thumbs/<layout>.png

uv run --no-project steps/thumbs.py   (after steps/art.py)
"""

import subprocess
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "out" / "thumbs"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
HEAD = """<!doctype html><meta charset=utf-8><link rel=stylesheet href="../fonts/fonts.css"><style>
* { margin: 0; } body { width: 1280px; height: 720px; overflow: hidden; background: #0b0f14; }
text { font-family: Inter, sans-serif; font-variant-ligatures: none; }</style><body>
<svg width="1280" height="720" viewBox="0 0 1280 720" xmlns="http://www.w3.org/2000/svg"><defs>
<pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M40 0H0V40" fill="none" stroke="#1a222c"/></pattern>
<radialGradient id="mg"><stop offset=".5" stop-color="#fff"/><stop offset="1" stop-color="#000"/></radialGradient>
<filter id="sh"><feDropShadow dx="0" dy="10" stdDeviation="12" flood-color="#000" flood-opacity=".6"/></filter>
</defs><rect width="1280" height="720" fill="url(#grid)"/>"""


def art(name: str, x: int, y: int, size: int) -> str:
    return (
        f'<mask id="m{x}"><rect x="{x}" y="{y}" width="{size}" height="{size}" fill="url(#mg)"/></mask>'
        f'<image href="art-{name}-crop.png" x="{x}" y="{y}" width="{size}" height="{size}" mask="url(#m{x})"/>'
    )


def split(name: str) -> str:
    return (
        HEAD
        + art(name, 690, 120, 560)
        + """
<g transform="rotate(-5 260 205)"><rect x="70" y="140" width="420" height="120" rx="24" fill="#1f9d4c" stroke="#2ee66b" stroke-width="5"/>
<text x="280" y="226" text-anchor="middle" style="font-family:'JetBrains Mono'" font-size="72" font-weight="700" fill="#fff">2 PASSED</text></g>
<text x="64" y="440" font-size="150" font-weight="900" letter-spacing="-5" fill="#fff" stroke="#000" stroke-width="6" paint-order="stroke">TESTS</text>
<text x="64" y="590" font-size="150" font-weight="900" letter-spacing="-5" fill="#ff3b3b" stroke="#000" stroke-width="6" paint-order="stroke">NOTHING</text></svg>"""
    )


def code_circle(name: str) -> str:
    return (
        HEAD
        + art(name, 860, 330, 400)
        + """
<g filter="url(#sh)"><rect x="60" y="250" width="860" height="200" rx="20" fill="#161b22" stroke="#30363d" stroke-width="3"/>
<text x="100" y="372" style="font-family:'JetBrains Mono'" font-size="58" fill="#e6edf3"><tspan fill="#ff7b72">assert</tspan> result == <tspan fill="#79c0ff">90.0</tspan></text></g>
<ellipse cx="712" cy="352" rx="150" ry="74" fill="none" stroke="#ff3b3b" stroke-width="10" transform="rotate(-6 640 352)"/>
<text x="60" y="170" font-size="120" font-weight="900" letter-spacing="-4" fill="#fff" stroke="#000" stroke-width="6" paint-order="stroke">FAKE TEST?</text>
<text x="60" y="590" font-size="64" font-weight="800" fill="#2ee66b">it passes. it checks nothing.</text></svg>"""
    )


def face_off(name: str) -> str:
    return (
        HEAD
        + art(name, 20, 60, 640)
        + """
<text x="700" y="250" font-size="132" font-weight="900" letter-spacing="-4" fill="#2ee66b" stroke="#000" stroke-width="6" paint-order="stroke">GREEN</text>
<text x="700" y="410" font-size="132" font-weight="900" fill="#fff" stroke="#000" stroke-width="6" paint-order="stroke">≠</text>
<text x="700" y="570" font-size="132" font-weight="900" letter-spacing="-4" fill="#ff3b3b" stroke="#000" stroke-width="6" paint-order="stroke">TESTED</text></svg>"""
    )


def shoot(markup: str, png: Path) -> None:
    src = png.with_suffix(".html")
    src.write_text(markup)
    subprocess.run(
        [
            CHROME,
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            "--window-size=1280,720",
            "--allow-file-access-from-files",
            "--virtual-time-budget=1500",
            f"--screenshot={png}",
            src.as_uri(),
        ],
        check=True,
        capture_output=True,
    )


if __name__ == "__main__":
    # art is center-cropped first: ffmpeg -i art-<s>.png -vf "crop=iw*0.62:ih*0.62:iw*0.19:ih*0.19" art-<s>-crop.png
    for style in ("glossy-cartoon", "flat-vector", "clay-3d"):
        shoot(split(style), OUT / f"split-{style}.png")
    shoot(code_circle("glossy-cartoon"), OUT / "layout-code-circle.png")
    shoot(face_off("glossy-cartoon"), OUT / "layout-face-off.png")
