"""PROTOTYPE: round 2 page: animated slides and revised writing rules. -> out/round2.html"""

from pathlib import Path

import markdown

HERE = Path(__file__).resolve().parent.parent
rules = markdown.markdown((HERE / "content" / "writing-rules.md").read_text())
clips = "".join(
    f'<label class="opt"><p><b>{n}</b></p><audio controls src="voice/markup-{n}.wav"></audio></label>'
    for n in ("ellipsis", "short-pause", "long-pause", "bracket", "slashes")
)


def pick(group: str, *values: str) -> str:
    return "".join(f'<label class="opt"><input type="radio" name="{group}" value="{v}"> {v}</label>' for v in values)


page = f"""<!doctype html><meta charset=utf-8><title>PROTOTYPE youtube-standards round 2</title>
<style>body{{font:15px -apple-system,sans-serif;background:#0d1117;color:#e6edf3;max-width:1300px;margin:auto;padding:16px}}
.banner{{background:#9e6a03;padding:8px 12px;font-weight:700;border-radius:6px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:12px;margin:10px 0}}
.opt{{display:block;background:#161b22;border:2px solid #30363d;border-radius:10px;padding:10px}}
.opt:has(input:checked){{border-color:#3fb950}} video,audio{{width:100%}} code{{color:#ffa657}}
textarea{{width:100%;height:120px;background:#161b22;color:#e6edf3}}</style>
<div class="banner">PROTOTYPE round 2: animated slides and writing rules</div>
<h2>A. Animated slides (Vox-style) vs static, same narration</h2>
<p>Puck, warm style, 0.92 pace, Lyria ambient bed at -30 dB, -14 LUFS. Animation: code typing, cursor move and click,
simulated test run, GREEN badge, zoom, highlight sweeps synced to words, callouts, clay art pop-in, function card with
NEVER RAN stamp. Built as one HTML page with Web Animations, rendered frame by frame (30 fps, 690 frames in about 25 s),
so every render is identical and timed from whisper word timestamps.</p>
<div class="grid"><label class="opt"><p><b>animated</b></p><video controls src="anim/animated.mp4"></video></label>
<label class="opt"><p><b>static</b></p><video controls src="anim/static.mp4"></video></label></div>
<div class="grid">{pick("animation", "animated-as-shown", "animated-more", "animated-less")}</div>
<h2>B. Pause markup test (Puck, warm)</h2><div class="grid">{clips}</div>
<h2>C. Revised writing rules</h2>{rules}
<div class="grid">{pick("rules", "agree", "edit-in-notes")}</div>
<h2>Notes</h2><textarea id="notes"></textarea>
<h2>Your picks</h2><textarea id="picks" readonly></textarea>
<script>const o=document.getElementById('picks');function u(){{o.value=[...document.querySelectorAll('input:checked')]
.map(i=>i.name+': '+i.value).concat(notes.value.trim()?['notes: '+notes.value.trim()]:[]).join('\\n')}}
document.addEventListener('change',u);document.addEventListener('input',u);</script>"""
(HERE / "out" / "round2.html").write_text(page)
print(HERE / "out" / "round2.html")
