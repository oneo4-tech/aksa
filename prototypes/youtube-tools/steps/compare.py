"""PROTOTYPE: build out/index.html, a side-by-side page to judge each tool option and copy the picks.

uv run steps/compare.py
"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
OUT = HERE / "out"
ENGINES = {
    "say": "macOS say (Samantha), free, offline",
    "gemini-gemini-3.8-flash-tts": "Gemini 3.8 Flash TTS (Charon), AI Studio key, plain text only",
    "gemini-gemini-2.5-flash-preview-tts": "Gemini 2.5 Flash TTS (Charon), AI Studio key, follows style prompt",
}
THUMBS = {
    "html.png": "HTML template rendered by Chrome: free, exact text, reusable, 2s",
    "gemini-2.5-flash-image.png": "Gemini 2.5 Flash Image: ignored 16:9, came back square",
    "gemini-3.1-flash-image-1280.png": "Gemini 3.1 Flash Image, resized to 1280x720: raster art, about 10s",
    "combined.png": "Combined: Claude SVG layout and text + Gemini 3.1 text-free art (steps/thumb_combined.html)",
    "claude-svg.png": "Designed by Claude as SVG (steps/thumb_claude.html): exact text, editable, free, 3s",
}


def timing(path: Path) -> str:
    return (
        " ".join(f"{k}={v}" for k, v in json.loads(path.read_text()).items() if k.endswith("seconds"))
        if path.exists()
        else ""
    )


def option(group: str, value: str, label: str, media: str) -> str:
    return (
        f'<label class="opt"><input type="radio" name="{group}" value="{value}">'
        f"<div>{media}<p><b>{value}</b><br>{label}</p></div></label>"
    )


def main() -> None:
    rows = []
    for video, tall in (("long", False), ("short1", True)):
        opts = "".join(
            option(
                f"voice-{video}",
                e,
                f"{d}<br><small>narrate {timing(OUT / video / e / 'timing.json')} | "
                f"{timing(OUT / video / f'{e}.timing.json')}</small>",
                f'<video controls preload="metadata" class="{"tall" if tall else "wide"}" src="{video}/{e}.mp4"></video>',
            )
            for e, d in ENGINES.items()
        )
        rows.append(
            f"<h2>{'Long-form' if not tall else 'Short'}: narration + edit + captions</h2><div class='grid'>{opts}</div>"
        )
    thumbs = "".join(option("thumbnail", t, d, f'<img src="thumbs/{t}">') for t, d in THUMBS.items())
    rows.append(f"<h2>Thumbnail</h2><div class='grid'>{thumbs}</div>")
    page = f"""<!doctype html><meta charset=utf-8><title>PROTOTYPE youtube-tools</title>
<style>
body {{ font: 15px -apple-system, sans-serif; background: #0d1117; color: #e6edf3; margin: 0 auto; max-width: 1400px; padding: 16px; }}
.banner {{ background: #9e6a03; color: #fff; padding: 8px 12px; font-weight: 700; border-radius: 6px; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px; }}
.opt {{ display: block; background: #161b22; border: 2px solid #30363d; border-radius: 10px; padding: 10px; cursor: pointer; }}
.opt:has(input:checked) {{ border-color: #3fb950; }} .opt input {{ float: right; }}
video.wide, img {{ width: 100%; }} video.tall {{ height: 480px; display: block; margin: auto; }}
small {{ color: #9da7b3; }} textarea {{ width: 100%; height: 120px; background: #161b22; color: #e6edf3; }}
</style>
<div class="banner">PROTOTYPE: throwaway, generated media, never committed</div>
<h1>Which tool per step?</h1>
<p>Question: for one sample video (Spot the Bug: an AI-written unit test that passes but tests nothing), which free or
already-paid option gives acceptable quality per step, and how long does each take? Pick one per group; the picks
text below updates for pasting back. Edit and captions are ffmpeg + whisper-cli in every video.</p>
{"".join(rows)}
<h2>Your picks</h2><textarea id="picks" readonly></textarea>
<script>
const out = document.getElementById('picks');
document.addEventListener('change', () => {{
  out.value = [...document.querySelectorAll('input:checked')].map(i => i.name + ': ' + i.value).join('\\n');
}});
</script>"""
    (OUT / "index.html").write_text(page)
    print(OUT / "index.html")


main()
