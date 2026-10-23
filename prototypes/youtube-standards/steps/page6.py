"""PROTOTYPE: round 6 page: logo colour combinations, evidence as links plus quotes, one description. -> out/round6.html"""

import html
import importlib.util
import json
from pathlib import Path

import markdown

HERE = Path(__file__).resolve().parent.parent
OUT = HERE / "out"
spec = importlib.util.spec_from_file_location("b", HERE / "steps" / "branding.py")
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)

cells = []
for sname, s in b.SYNTAX_COLORS.items():
    for nname, n in b.NAME_COLORS.items():
        if s.lower() == n.lower():
            continue
        p = {"syntax": s, "name": n, "suffix": "#00e5ff"}
        body, width = b.wordmark(p, "testlab")
        cells.append(
            f'<label class="opt"><input type="radio" name="logo" value="{sname} + {nname}">'
            f'<svg viewBox="-10 16 {width} 132">{body}</svg><svg class="i" viewBox="2 -18 200 200">{b.icon(p)}</svg>'
            f"<small>&lt;/&gt; {sname} {s} &middot; oneo4 {nname} {n}</small></label>"
        )

ev = json.loads((OUT / "evidence" / "evidence.json").read_text())
ev_rows = "".join(
    f"<li><b>{e['claim']}</b> &ldquo;{html.escape(e['quote'])}&rdquo; &mdash; "
    f'<a href="{html.escape(e["link"])}" target=_blank>{html.escape(e["url"])}</a> '
    f"<small>({'exact match' if e['found_exact'] else 'NOT FOUND'}, checked {e['checked'][:10]})</small></li>"
    for e in ev
)
desc = markdown.markdown((HERE / "content" / "channel-description.md").read_text())
page = f"""<!doctype html><meta charset=utf-8><title>PROTOTYPE youtube-standards round 6</title>
<style>body{{font:15px -apple-system,sans-serif;background:#0d1117;color:#e6edf3;max-width:1500px;margin:auto;padding:16px}}
.banner{{background:#9e6a03;padding:8px 12px;font-weight:700;border-radius:6px}} a{{color:#58a6ff}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(440px,1fr));gap:12px}}
.opt{{display:grid;grid-template-columns:1fr 70px;gap:8px;align-items:center;background:#000;border:2px solid #222;
border-radius:10px;padding:10px;cursor:pointer}} .opt small{{grid-column:1/3;color:#888}} .opt input{{position:absolute;opacity:0}}
.opt:has(input:checked){{border-color:#3fb950}} svg{{width:100%}} li{{margin:6px 0}}
textarea{{width:100%;height:110px;background:#161b22;color:#e6edf3}}</style>
<div class="banner">PROTOTYPE round 6: logo colours, evidence format, description</div>
<h2>A. Logo colour: &lt; / &gt; and 4 stroke vs oneo4 letters (black background, cyan testlab suffix)</h2>
<div class="grid">{"".join(cells)}</div>
<h2>B. Evidence format: link opening at the quote, plus the quoted line (no screenshots)</h2>
<p>Each quote is still checked automatically for an exact match on the live page.</p><ol>{ev_rows}</ol>
<h2>C. Channel description: one channel; D1 and D2 are two wordings of its single description</h2>{desc}
<div class="grid"><label class="opt"><input type="radio" name="description" value="D1-short"> D1 short</label>
<label class="opt"><input type="radio" name="description" value="D2-structured"> D2 structured</label></div>
<h2>Notes</h2><textarea id="notes"></textarea><h2>Your picks</h2><textarea id="picks" readonly></textarea>
<script>const o=document.getElementById('picks');function u(){{o.value=[...document.querySelectorAll('input:checked')]
.map(i=>i.name+': '+i.value).concat(notes.value.trim()?['notes: '+notes.value.trim()]:[]).join('\\n')}}
document.addEventListener('change',u);document.addEventListener('input',u);</script>"""
(OUT / "round6.html").write_text(page)
