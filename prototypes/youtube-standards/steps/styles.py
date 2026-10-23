"""PROTOTYPE: visual themes x slide kinds, and code-presentation variants, rendered by headless Chrome.

uv run --no-project steps/styles.py -> out/visual/<theme>-<kind>.png, out/slides/<variant>.png
"""

import html
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
OUT = HERE / "out"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
FONTS = "../fonts/fonts.css"  # Google Fonts (OFL), cached locally by curl into out/fonts
THEMES = {
    "github-dark": {
        "bg": "#0d1117",
        "panel": "#161b22",
        "border": "#30363d",
        "fg": "#e6edf3",
        "muted": "#9da7b3",
        "accent": "#3fb950",
        "bad": "#f85149",
        "key": "#ff7b72",
        "str": "#a5d6ff",
        "num": "#79c0ff",
        "ui": "Inter",
        "mono": "JetBrains Mono",
        "note": "Dark, GitHub-like: familiar to developers",
    },
    "lab-notebook": {
        "bg": "#f6f3ea",
        "panel": "#ffffff",
        "border": "#d9d2c0",
        "fg": "#1d1d1f",
        "muted": "#5c5a55",
        "accent": "#d9480f",
        "bad": "#c92a2a",
        "key": "#7b2cbf",
        "str": "#2b8a3e",
        "num": "#1864ab",
        "ui": "IBM Plex Sans",
        "mono": "IBM Plex Mono",
        "note": "Light paper, warm orange: calm, editorial",
    },
    "neon-terminal": {
        "bg": "#07070c",
        "panel": "#10101a",
        "border": "#2a2a40",
        "fg": "#f2f2ff",
        "muted": "#9a9ab8",
        "accent": "#00e5ff",
        "bad": "#ff2e88",
        "key": "#ff2e88",
        "str": "#ffe066",
        "num": "#00e5ff",
        "ui": "Space Grotesk",
        "mono": "Fira Code",
        "note": "Near-black with cyan and magenta: bold, high energy",
    },
}
CODE = """def test_apply_discount():
    with patch.object(discount, "apply_discount", return_value=90.0) as fake:
        result = discount.apply_discount(100, 10)
    assert result == 90.0
    fake.assert_called_once()


def test_apply_discount_runs():
    result = discount.apply_discount(100, 10)
    assert result is not None"""
FOCUS = {2, 3, 4}
KEYWORDS = r"\b(def|return|import|from|with|as|assert|if|not|raise|is|None)\b"


def highlight(code: str) -> list[str]:
    lines = []
    for line in html.escape(code).splitlines():
        line = re.sub(r"(&quot;.*?&quot;)", r'<span class="s">\1</span>', line)
        line = re.sub(KEYWORDS, r'<span class="k">\1</span>', line)
        line = re.sub(r"\b(\d+(\.\d+)?)\b", r'<span class="n">\1</span>', line)
        lines.append(line or " ")
    return lines


def css(t: dict, w: int, h: int) -> str:
    return f"""
* {{ margin: 0; box-sizing: border-box; }}
body {{ width: {w}px; height: {h}px; background: {t["bg"]}; color: {t["fg"]}; font-family: '{t["ui"]}', sans-serif;
  padding: 150px 120px 100px; display: flex; flex-direction: column; gap: 44px; position: relative; overflow: hidden; }}
.brand {{ position: absolute; top: 64px; left: 120px; font: 700 26px '{t["mono"]}', monospace; color: {t["accent"]}; }}
.brand b {{ color: {t["muted"]}; font-weight: 400; }}
h1 {{ font-size: 84px; font-weight: 800; letter-spacing: -2px; line-height: 1.05; }}
.sub {{ font-size: 44px; color: {t["muted"]}; }}
.points div {{ font-size: 46px; line-height: 1.7; }}
.points div::before {{ content: '→ '; color: {t["accent"]}; font-weight: 700; }}
pre {{ background: {t["panel"]}; border: 2px solid {t["border"]}; border-radius: 18px; padding: 36px 40px;
  font: 30px/1.55 '{t["mono"]}', monospace; position: relative; font-variant-ligatures: none; }}
.k {{ color: {t["key"]}; }} .s {{ color: {t["str"]}; }} .n {{ color: {t["num"]}; }}
.pass {{ color: {t["accent"]}; font-weight: 700; }} .fail {{ color: {t["bad"]}; font-weight: 700; }}
.dim {{ opacity: .28; }} .hl {{ background: {t["accent"]}22; box-shadow: inset 6px 0 {t["accent"]}; display: block; margin: 0 -40px; padding: 0 40px; }}
.callout {{ position: absolute; right: 60px; background: {t["bad"]}; color: #fff; font: 700 30px '{t["ui"]}', sans-serif;
  padding: 14px 22px; border-radius: 12px; }}
.big {{ font-size: 140px; font-weight: 900; letter-spacing: -4px; line-height: .95; }}
.big span {{ color: {t["bad"]}; }}
.mark {{ display: inline-block; background: {t["accent"]}; color: {t["bg"]}; font: 800 40px '{t["mono"]}', monospace;
  padding: 10px 26px; border-radius: 14px; }}
"""


def page(t: dict, body: str, w: int = 1920, h: int = 1080) -> str:
    return (
        f'<!doctype html><meta charset=utf-8><link rel=stylesheet href="{FONTS}"><style>{css(t, w, h)}</style>'
        f'<body><div class="brand">OneO4TestLab <b>/ PROTOTYPE</b></div>{body}</body>'
    )


def kinds(t: dict) -> dict[str, str]:
    code = "\n".join(highlight(CODE))
    return {
        "title": '<div style="margin-top:120px"><div class="mark">SPOT THE BUG</div></div>'
        '<div class="big">Two green tests.<br><span>Zero protection.</span></div>',
        "code": f"<h1>The AI-written tests</h1><pre>{code}</pre>",
        "points": "<h1>Bug one: it tests the mock</h1><div class='points'><div>patch.object replaces the function"
        "</div><div>The assertion checks the fake's value</div><div>The real code never runs</div></div>",
        "terminal": "<h1>Prove it: break the code</h1><pre>$ ./mutate.sh\n\n== AI tests vs broken code ==\n"
        "<span class='pass'>2 passed</span>\n== Real tests vs broken code ==\n"
        "<span class='fail'>2 failed</span>, <span class='pass'>2 passed</span></pre>",
    }


def code_variants(t: dict) -> dict[str, str]:
    lines = highlight(CODE)
    full = "\n".join(lines)
    focus = "\n".join(
        f'<span class="hl">{ln}</span>' if i in FOCUS else f'<span class="dim">{ln}</span>'
        for i, ln in enumerate(lines, 1)
    )
    snippet = "\n".join(lines[1:4])
    return {
        "a-full-file": f"<h1>The AI-written tests</h1><pre>{full}</pre>",
        "b-focus-lines": f"<h1>Look at lines 2 to 4</h1><pre>{focus}</pre>",
        "c-zoom-callout": "<h1>It tests the mock</h1><pre style='font-size:35px;margin-top:40px'>"
        f"{snippet}<div class='callout' style='top:-34px'>fake returns 90</div>"
        "<div class='callout' style='bottom:-30px'>…then asserts 90</div></pre>",
    }


def shoot(markup: str, png: Path, w: int = 1920, h: int = 1080) -> None:
    src = png.with_suffix(".html")
    src.write_text(markup)
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


def main() -> None:
    (OUT / "visual").mkdir(parents=True, exist_ok=True)
    (OUT / "slides").mkdir(parents=True, exist_ok=True)
    for name, t in THEMES.items():
        for kind, body in kinds(t).items():
            shoot(page(t, body), OUT / "visual" / f"{name}-{kind}.png")
    for name, body in code_variants(THEMES["github-dark"]).items():
        shoot(page(THEMES["github-dark"], body), OUT / "slides" / f"{name}.png")


if __name__ == "__main__":
    main()
