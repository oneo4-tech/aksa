"""PROTOTYPE: render scene slides and HTML thumbnails to PNG with headless Chrome.

uv run steps/render.py slides <scenes.json>      -> out/<video>/slides/NN.png
uv run steps/render.py thumb                     -> out/thumbs/html.png
"""

import html
import json
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
KEYWORDS = r"\b(def|return|import|from|with|as|assert|if|not|raise|for|in|is|None|True|False)\b"

CSS = """
* { margin: 0; box-sizing: border-box; }
body { width: %(w)dpx; height: %(h)dpx; background: #0d1117; color: #e6edf3;
  font-family: -apple-system, 'Helvetica Neue', sans-serif; display: flex; flex-direction: column;
  justify-content: flex-start; padding: %(top)dpx %(pad)dpx %(pad)dpx; gap: %(gap)dpx; }
.brand { position: absolute; top: %(bt)dpx; left: %(pad)dpx; color: #3fb950; font: 600 %(bs)dpx ui-monospace, Menlo, monospace; }
h1 { font-size: %(h1)dpx; line-height: 1.1; }
.body { font-size: %(bf)dpx; color: #9da7b3; white-space: pre-line; line-height: 1.4; }
.points { font-size: %(bf)dpx; line-height: 1.6; }
.points div::before { content: '> '; color: #3fb950; }
pre { background: #161b22; border: 2px solid #30363d; border-radius: 16px; padding: %(cp)dpx;
  font: %(cf)dpx/1.45 ui-monospace, Menlo, monospace; white-space: pre-wrap; }
.term { color: #e6edf3; } .pass { color: #3fb950; } .fail { color: #f85149; }
.k { color: #ff7b72; } .s { color: #a5d6ff; } .c { color: #8b949e; } .n { color: #79c0ff; }
"""


def sizes(fmt: str) -> dict:
    w, h = map(int, fmt.split("x"))
    tall = h > w
    return {
        "w": w,
        "h": h,
        "top": 420 if tall else 170,
        "pad": 90 if tall else 120,
        "gap": 60 if tall else 48,
        "bt": 80,
        "bs": 34 if tall else 28,
        "h1": 104 if tall else 80,
        "bf": 54 if tall else 46,
        "cf": 34 if tall else 28,
        "cp": 40,
    }


def highlight(code: str) -> str:
    out = []
    for line in html.escape(code).splitlines():
        if line.lstrip().startswith("#") or line.lstrip().startswith("&quot;&quot;&quot;"):
            out.append(f'<span class="c">{line}</span>')
            continue
        line = re.sub(r"(&quot;.*?&quot;)", r'<span class="s">\1</span>', line)
        line = re.sub(KEYWORDS, r'<span class="k">\1</span>', line)
        line = re.sub(r"\b(\d+(\.\d+)?)\b", r'<span class="n">\1</span>', line)
        out.append(line)
    return "\n".join(out)


def terminal(text: str) -> str:
    rows = []
    for line in html.escape(text).splitlines():
        cls = "fail" if "failed" in line else "pass" if "passed" in line else "term"
        rows.append(f'<span class="{cls}">{line}</span>')
    return "\n".join(rows)


def page(scene: dict, fmt: str) -> str:
    s = sizes(fmt)
    parts = [f'<div class="brand">OneO4TestLab / PROTOTYPE</div><h1>{html.escape(scene["heading"])}</h1>']
    if scene["kind"] == "code":
        text = scene.get("code") or re.sub(r'^""\".*?""\"\n+', "", (HERE / scene["file"]).read_text(), flags=re.DOTALL)
        lines = text.splitlines()
        if "lines" in scene and "code" not in scene:
            a, b = scene["lines"]
            lines = lines[a - 1 : b]
        parts.append(f"<pre>{highlight(chr(10).join(lines))}</pre>")
    elif scene["kind"] == "terminal":
        parts.append(f"<pre>{terminal(scene['body'])}</pre>")
    elif scene["kind"] == "points":
        parts.append(
            '<div class="points">'
            + "".join(f"<div>{html.escape(p)}</div>" for p in scene["body"].splitlines())
            + "</div>"
        )
    else:
        parts.append(f'<div class="body">{html.escape(scene.get("body", ""))}</div>')
    return f"<!doctype html><meta charset=utf-8><style>{CSS % s}</style><body>{''.join(parts)}</body>"


def shoot(page_html: str, fmt: str, png: Path) -> None:
    src = png.with_suffix(".html")
    src.write_text(page_html)
    w, h = fmt.split("x")
    subprocess.run(
        [
            CHROME,
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            f"--window-size={w},{h}",
            f"--screenshot={png}",
            src.as_uri(),
        ],
        check=True,
        capture_output=True,
    )


def slides(scenes_file: Path) -> None:
    video = json.loads(scenes_file.read_text())
    out = HERE / "out" / video["id"] / "slides"
    out.mkdir(parents=True, exist_ok=True)
    start = time.time()
    for i, scene in enumerate(video["scenes"]):
        shoot(page(scene, video["format"]), video["format"], out / f"{i:02d}.png")
    print(
        json.dumps(
            {"step": "slides", "engine": "html-chrome", "video": video["id"], "seconds": round(time.time() - start, 1)}
        )
    )


THUMB = """<!doctype html><meta charset=utf-8><style>
* { margin: 0; } body { width: 1280px; height: 720px; background: #0d1117; font-family: -apple-system, sans-serif;
  display: grid; grid-template-columns: 1fr 1fr; align-items: center; overflow: hidden; }
.l { padding-left: 70px; } .badge { display: inline-block; background: #238636; color: #fff; font: 800 96px ui-monospace, Menlo, monospace;
  padding: 18px 36px; border-radius: 22px; transform: rotate(-4deg); box-shadow: 0 0 80px #3fb95088; }
h1 { color: #fff; font-size: 128px; line-height: .95; font-weight: 900; margin-top: 50px; letter-spacing: -3px; }
h1 span { color: #f85149; } .r { font-size: 380px; text-align: center; filter: drop-shadow(0 0 60px #f8514988); }
</style><body><div class="l"><div class="badge">2 PASSED</div><h1>TESTS<br><span>NOTHING</span></h1></div><div class="r">&#x1F41E;</div></body>"""


def thumb() -> None:
    out = HERE / "out" / "thumbs"
    out.mkdir(parents=True, exist_ok=True)
    start = time.time()
    shoot(THUMB, "1280x720", out / "html.png")
    print(json.dumps({"step": "thumbnail", "engine": "html-chrome", "seconds": round(time.time() - start, 1)}))


if sys.argv[1] == "slides":
    slides(Path(sys.argv[2]))
else:
    thumb()
