"""PROTOTYPE: round 4 page: citation dossier, advice review, voice identity options. -> out/round4.html"""

from pathlib import Path

import markdown

HERE = Path(__file__).resolve().parent.parent


def md(name: str) -> str:
    return markdown.markdown((HERE / "content" / name).read_text(), extensions=["tables"])


def pick(group: str, options: list[tuple[str, str]]) -> str:
    return (
        '<div class="grid">'
        + "".join(
            f'<label class="opt"><input type="radio" name="{group}" value="{v}"> <b>{v}</b> {d}</label>'
            for v, d in options
        )
        + "</div>"
    )


voices = "".join(
    f'<label class="opt"><input type="radio" name="voice-identity" value="{v}"> <b>{v}</b> {d}'
    f'<audio controls src="voice/designed-{f}.wav"></audio></label>'
    for v, d, f in [
        ("puck", "prebuilt Puck, warm (current pick)", "puck-baseline"),
        ("designed-architect", "calm senior architect, light Indian English accent", "architect"),
        ("designed-mentor", "warm curious tester, US English", "mentor"),
        ("designed-lead", "crisp QA lead, British English", "lead"),
    ]
)
import html
import json

W = {"lens": 3, "proof": 3, "fresh": 2, "pull": 2, "distinct": 2, "effort": 1}
rows = []
for i in json.loads((HERE / "content" / "backlog-sample.json").read_text()):
    if i["id"] < 17:
        continue
    t = sum(W[k] * v for k, v in i["scores"].items())
    e = {k: html.escape(str(v)) for k, v in i.items() if k != "scores"}
    risk = f"<br><b>Risk:</b> {e['risk']}" if "risk" in i else ""
    radios = "".join(
        f'<label><input type="radio" name="idea-{i["id"]}" value="{v}"> {v}</label> '
        for v in ("approve", "later", "drop")
    )
    rows.append(
        f"<tr><td><b>{t}</b></td><td><b>{e['title']}</b><br><small>{e['pillar']} | {e['format']}</small></td>"
        f"<td><b>Lens:</b> {e['rst']}<br><b>Tester asks:</b> {e['question']}<br><b>Proof:</b> {e['proof']}{risk}</td><td>{radios}</td></tr>"
    )
new_ideas = "<table>" + "".join(rows) + "</table>"
page = f"""<!doctype html><meta charset=utf-8><title>PROTOTYPE youtube-standards round 4</title>
<style>body{{font:15px -apple-system,sans-serif;background:#0d1117;color:#e6edf3;max-width:1300px;margin:auto;padding:16px}}
.banner{{background:#9e6a03;padding:8px 12px;font-weight:700;border-radius:6px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px;margin:10px 0}}
.opt{{display:block;background:#161b22;border:2px solid #30363d;border-radius:10px;padding:10px}}
.opt:has(input:checked){{border-color:#3fb950}} audio{{width:100%}} td,th{{border:1px solid #30363d;padding:6px 8px;vertical-align:top}}
table{{border-collapse:collapse}} a{{color:#58a6ff}} textarea{{width:100%;height:120px;background:#161b22;color:#e6edf3}}</style>
<div class="banner">PROTOTYPE round 4: citations, advice review, voice identity</div>
<h2>A. Citation dossier (sample for idea 2)</h2>{md("dossier-idea-2.md")}
{pick("dossier", [("agree", "use this dossier format for every video"), ("edit-in-notes", "")])}
<h2>B. Voice identity (same line, // pauses, warm style)</h2>
<p>Designed voices are stored in your Google project for 1 year. Your own replicated voice needs a 10-30 s clean speech
clip and a consent clip from you (Google AI Studio has a recorder); YouTube exempts cloning your own voice from AI
disclosure.</p><div class="grid">{voices}
<label class="opt"><input type="radio" name="voice-identity" value="replicate-own"> <b>replicate my own voice</b>
(I will record the clips in AI Studio)</label></div>
<h2>C. Review of the pasted advice</h2>{md("advice-review.md")}
<h3>Decisions</h3>
{pick("shorts-mix", [("1-long-2-shorts", "keep, Shorts link to the long-form; pilot measures"), ("long-first", "long-form only until watch hours grow")])}
{pick("voice-tone", [("warm", "current"), ("calm-authoritative", "senior architect tone")])}
{pick("tools-pillar", [("add", "Tools under test: real, versioned tools, RST lens"), ("skip", "")])}
{pick("revenue", [("later", "separate work request after the pilot"), ("now", "add affiliate and product slots now")])}
{pick("visual-pace", [("3-5s", "visual change every 3-5 s"), ("2-3-sentences", "keep")])}
<h2>E. New backlog ideas (your additions, scored)</h2>{new_ideas}
<h2>D. Competitive research</h2><p>Blocked: <code>GOOGLE_CLOUD_API_KEY</code> is not a standard API key (it does not start
with AIza), and the YouTube Data API returns 401. Create one in Google Cloud Console: APIs and Services, Credentials,
Create credentials, API key, restrict it to YouTube Data API v3, and replace the value in .env.</p>
<h2>Notes</h2><textarea id="notes"></textarea><h2>Your picks</h2><textarea id="picks" readonly></textarea>
<script>const o=document.getElementById('picks');function u(){{o.value=[...document.querySelectorAll('input:checked')]
.map(i=>i.name+': '+i.value).concat(notes.value.trim()?['notes: '+notes.value.trim()]:[]).join('\\n')}}
document.addEventListener('change',u);document.addEventListener('input',u);</script>"""
(HERE / "out" / "round4.html").write_text(page)
