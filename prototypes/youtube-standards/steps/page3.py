"""PROTOTYPE: round 3 page: animated-more and the backlog research strategy with a scored sample backlog.

uv run --no-project --with markdown steps/page3.py -> out/round3.html
"""

import html
import json
from pathlib import Path

import markdown

HERE = Path(__file__).resolve().parent.parent
WEIGHTS = {"lens": 3, "proof": 3, "fresh": 2, "pull": 2, "distinct": 2, "effort": 1}

strategy = markdown.markdown((HERE / "content" / "backlog-strategy.md").read_text(), extensions=["tables"])
ideas = json.loads((HERE / "content" / "backlog-sample.json").read_text())
for i in ideas:
    i["total"] = sum(WEIGHTS[k] * v for k, v in i["scores"].items())
ideas.sort(key=lambda i: -i["total"])

rows = []
for i in ideas:
    e = {k: html.escape(str(v)) for k, v in i.items() if k != "scores"}
    s = " ".join(f"{k} {v}" for k, v in i["scores"].items())
    risk = f"<br><b>Risk:</b> {e['risk']}" if "risk" in i else ""
    picks = "".join(
        f'<label><input type="radio" name="idea-{i["id"]}" value="{v}"> {v}</label> '
        for v in ("approve", "later", "drop")
    )
    rows.append(f"""<tr><td><b>{i["total"]}</b></td><td><b>{e["title"]}</b><br><small>{e["pillar"]} | {e["format"]}</small></td>
<td><b>Lens:</b> {e["rst"]}<br><b>Claim:</b> {e["claim"]}<br><b>Tester asks:</b> {e["question"]}<br><b>Proof:</b> {e["proof"]}
<br><b>Hook:</b> {e["hook"]}{risk}<br><small>{s}</small></td><td>{picks}</td></tr>""")

page = f"""<!doctype html><meta charset=utf-8><title>PROTOTYPE youtube-standards round 3</title>
<style>body{{font:15px -apple-system,sans-serif;background:#0d1117;color:#e6edf3;max-width:1400px;margin:auto;padding:16px}}
.banner{{background:#9e6a03;padding:8px 12px;font-weight:700;border-radius:6px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(380px,1fr));gap:12px}}
.opt{{display:block;background:#161b22;border:2px solid #30363d;border-radius:10px;padding:10px}}
.opt:has(input:checked){{border-color:#3fb950}} video{{width:100%}} td,th{{border:1px solid #30363d;padding:6px 8px;vertical-align:top}}
table{{border-collapse:collapse}} textarea{{width:100%;height:140px;background:#161b22;color:#e6edf3}}</style>
<div class="banner">PROTOTYPE round 3: animation intensity and backlog research</div>
<h2>A. Animation: as shown vs more</h2>
<p>"More" adds a slow camera drift, kinetic words with a dark veil ("GREEN." "PASSING."), an arrow drawn between the two 90s,
and an animated call-flow diagram showing the real function never called.</p>
<div class="grid">
<label class="opt"><input type="radio" name="animation" value="as-shown"> <b>as shown</b><video controls src="anim/animated.mp4"></video></label>
<label class="opt"><input type="radio" name="animation" value="more"> <b>more</b><video controls src="anim/animated-more.mp4"></video></label>
<label class="opt"><input type="radio" name="animation" value="mix"> <b>mix</b>: as shown, plus chosen "more" effects (say which in notes)</label></div>
<h2>B. Backlog research strategy</h2>{strategy}
<label class="opt"><input type="radio" name="strategy" value="agree"> agree</label>
<label class="opt"><input type="radio" name="strategy" value="edit-in-notes"> edit in notes</label>
<h2>C. Sample backlog, ranked by score (max 65)</h2>
<table><tr><th>Score</th><th>Idea</th><th>Tester's angle</th><th>Pick</th></tr>{"".join(rows)}</table>
<h2>Notes</h2><textarea id="notes"></textarea>
<h2>Your picks</h2><textarea id="picks" readonly></textarea>
<script>const o=document.getElementById('picks');function u(){{o.value=[...document.querySelectorAll('input:checked')]
.map(i=>i.name+': '+i.value).concat(notes.value.trim()?['notes: '+notes.value.trim()]:[]).join('\\n')}}
document.addEventListener('change',u);document.addEventListener('input',u);</script>"""
(HERE / "out" / "round3.html").write_text(page)
print(", ".join(f"{i['id']}:{i['total']}" for i in ideas))
