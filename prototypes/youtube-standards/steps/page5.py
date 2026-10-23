"""PROTOTYPE: round 5 page: evidence dossier, competitive research, channel branding. -> out/round5.html"""

import html
import json
from pathlib import Path

import markdown

HERE = Path(__file__).resolve().parent.parent
OUT = HERE / "out"


def pick(group: str, options: list[tuple[str, str]], media: dict | None = None) -> str:
    media = media or {}
    return (
        '<div class="grid">'
        + "".join(
            f'<label class="opt"><input type="radio" name="{group}" value="{v}"> <b>{v}</b> {d}{media.get(v, "")}</label>'
            for v, d in options
        )
        + "</div>"
    )


ev = json.loads((OUT / "evidence" / "evidence.json").read_text())
ev_rows = "".join(
    f"<tr><td><b>{e['claim']}</b></td><td>&ldquo;{html.escape(e['quote'])}&rdquo;<br>"
    f'<a href="{html.escape(e["link"])}" target=_blank>open at quote</a> &middot; <a href="{e["url"]}" target=_blank>'
    f"{html.escape(e['url'])}</a><br><small>exact match: {'yes' if e['found_exact'] else 'NO'} &middot; checked "
    f'{e["checked"]} &middot; snapshot sha256 {e["sha256"]} &middot; <a href="evidence/{e["claim"]}.txt">page text</a>'
    f'</small></td><td><a href="evidence/{e["claim"]}.png" target=_blank><img src="evidence/{e["claim"]}.png"></a></td></tr>'
    for e in ev
)

comp = json.loads((OUT / "competition" / "competition-filtered.json").read_text())
ideas = {i["id"]: i["title"] for i in json.loads((HERE / "content" / "backlog-sample.json").read_text())}
comp_html = ""
for k, v in comp.items():
    vids = sorted(v["videos"], key=lambda x: -x["views"])
    views = sorted(x["views"] for x in vids)
    med = views[len(views) // 2] if views else 0
    head = (
        f"<summary><b>{k}. {html.escape(ideas.get(int(k), ''))}</b> &middot; query <code>{html.escape(v['query'])}"
        f"</code> &middot; {len(vids)} topical videos, median views {med:,}, "
        f"{sum(x['published'] >= '2025-10-23' for x in vids)} in last 12 months</summary>"
    )
    rows = "".join(
        f"<tr><td>{x['views']:,}</td><td>{x['views_per_day']:,}</td><td>{x['minutes']}</td><td>{x['published']}"
        f'</td><td><a href="{x["url"]}" target=_blank>{html.escape(x["title"])}</a></td>'
        f"<td>{html.escape(x['channel'])}</td></tr>"
        for x in vids[:8]
    )
    comp_html += (
        f"<details>{head}<table><tr><th>Views</th><th>/day</th><th>Min</th><th>Published</th><th>Title</th>"
        f"<th>Channel</th></tr>{rows or '<tr><td colspan=6>No topical match: open niche or query to refine'}"
        f"</table></details>"
    )

brand = {
    p: (
        f'<img src="branding/{p}-avatar.png" style="width:30%"><img src="branding/{p}-banner-guides.png">'
        f'<img src="branding/{p}-testlab.png"><img src="branding/{p}-aksa.png">'
    )
    for p in ("spec-red", "neon", "red-cyan")
}
desc = markdown.markdown((HERE / "content" / "channel-description.md").read_text())

page = f"""<!doctype html><meta charset=utf-8><title>PROTOTYPE youtube-standards round 5</title>
<style>body{{font:15px -apple-system,sans-serif;background:#0d1117;color:#e6edf3;max-width:1400px;margin:auto;padding:16px}}
.banner{{background:#9e6a03;padding:8px 12px;font-weight:700;border-radius:6px}} a{{color:#58a6ff}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(380px,1fr));gap:12px;margin:10px 0}}
.opt{{display:block;background:#161b22;border:2px solid #30363d;border-radius:10px;padding:10px}}
.opt:has(input:checked){{border-color:#3fb950}} img{{width:100%;margin-top:6px}} td,th{{border:1px solid #30363d;padding:6px;vertical-align:top}}
table{{border-collapse:collapse;width:100%}} td img{{width:420px}} details{{margin:6px 0}} summary{{cursor:pointer}}
textarea{{width:100%;height:120px;background:#161b22;color:#e6edf3}}</style>
<div class="banner">PROTOTYPE round 5: evidence, competition, branding</div>
<h2>A. Evidence dossier (idea 2): every quote checked live, highlighted, snapshotted</h2>
<p>"open at quote" uses a text-fragment link: Chrome scrolls to and highlights the quoted words. Screenshots show the
source page with the quote outlined. Page text snapshots and their SHA-256 let you see if a source changes later.
Claims and statuses: <code>content/dossier-idea-2.md</code>.</p>
<table><tr><th>Claim</th><th>Quote and links</th><th>Screenshot</th></tr>{ev_rows}</table>
{pick("dossier", [("agree", "use this evidence format for every video"), ("edit-in-notes", "")])}
<h2>B. Competitive research (YouTube Data API, 2026-10-23)</h2>
<p>Closest videos per idea, filtered to topical titles. Quota note: search allows 100 calls a day; results are now
cached per query. Ideas with no match get refined queries tomorrow.</p>{comp_html}
<h2>C. Channel branding (from oneo4 logo spec v0.4)</h2>
<p>Avatar 800x800 (renders at 98x98), banner 2048x1152 with the 1235x338 safe area outlined, wordmarks for testlab and
aksa, plus a 150x150 watermark per palette in <code>out/branding/</code>.</p>
{
    pick(
        "palette",
        [
            ("spec-red", "spec: Signal Red syntax, white letters, black"),
            ("neon", "matches videos: magenta syntax, cyan suffix, near-black"),
            ("red-cyan", "spec red syntax with the videos' cyan suffix"),
        ],
        brand,
    )
}
<h2>D. Channel description</h2>{desc}
{pick("description", [("D1-short", ""), ("D2-structured", "")])}
<h2>Notes</h2><textarea id="notes"></textarea><h2>Your picks</h2><textarea id="picks" readonly></textarea>
<script>const o=document.getElementById('picks');function u(){{o.value=[...document.querySelectorAll('input:checked')]
.map(i=>i.name+': '+i.value).concat(notes.value.trim()?['notes: '+notes.value.trim()]:[]).join('\\n')}}
document.addEventListener('change',u);document.addEventListener('input',u);</script>"""
(OUT / "round5.html").write_text(page)
