"""PROTOTYPE: YouTube competitive research per approved idea (YouTube Data API v3, GOOGLE_CLOUD_API_KEY).

uv run --no-project steps/competition.py -> out/competition/competition.json and competition.md
Quota: search.list 1 unit in the Search Queries bucket (100 calls/day); videos.list 1 unit.
"""

import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
OUT = HERE / "out" / "competition"
API = "https://www.googleapis.com/youtube/v3/"
QUERIES = {
    1: "AI generated unit tests mutation testing",
    2: "Playwright test agents healer",
    3: "Cypress cy.prompt self healing",
    4: "test oracles heuristics HICCUPPS",
    5: "LLM sycophancy code review",
    6: "LLM consistency testing same prompt",
    7: "SFDIPOT heuristic test strategy model",
    8: "bug report writing safety language",
    9: "Copilot coding agent tests validation",
    10: "prompt injection testing OWASP LLM01",
    11: "excessive agency AI agent testing OWASP",
    12: "100% code coverage misleading",
    14: "LLM evals vs testing",
    15: "will AI replace software testers",
    16: "Post Office Horizon scandal software testing",
}


def get(endpoint: str, **params: str) -> dict:
    params["key"] = os.environ["GOOGLE_CLOUD_API_KEY"]
    url = API + endpoint + "?" + urllib.parse.urlencode(params)
    try:
        return json.load(urllib.request.urlopen(url, timeout=60))
    except urllib.error.HTTPError as e:
        sys.exit(f"{endpoint}: {e.code} {e.read().decode()[:300]}")


def seconds(iso: str) -> int:
    m = re.fullmatch(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso)
    d, h, mi, s = (int(x or 0) for x in m.groups())
    return d * 86400 + h * 3600 + mi * 60 + s


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    now = datetime.now(UTC)
    report = {}
    for idea, q in QUERIES.items():
        found = get("search", part="id", type="video", q=q, maxResults="10", relevanceLanguage="en", order="relevance")
        ids = [i["id"]["videoId"] for i in found.get("items", [])]
        if not ids:
            report[idea] = {"query": q, "videos": []}
            continue
        vids = get("videos", part="snippet,statistics,contentDetails", id=",".join(ids))["items"]
        rows = []
        for v in vids:
            published = datetime.fromisoformat(v["snippet"]["publishedAt"])
            age = max((now - published).days, 1)
            views = int(v["statistics"].get("viewCount", 0))
            rows.append(
                {
                    "title": v["snippet"]["title"],
                    "channel": v["snippet"]["channelTitle"],
                    "url": f"https://www.youtube.com/watch?v={v['id']}",
                    "published": published.date().isoformat(),
                    "views": views,
                    "views_per_day": round(views / age, 1),
                    "minutes": round(seconds(v["contentDetails"]["duration"]) / 60, 1),
                }
            )
        report[idea] = {"query": q, "videos": rows}
        print(idea, q, len(rows), file=sys.stderr)
    (OUT / "competition.json").write_text(json.dumps(report, indent=1))

    lines = [
        "# PROTOTYPE: competitive research per idea",
        "",
        (
            f"YouTube Data API v3 search.list (relevance, English) and videos.list, run {now.date()}. "
            "Up to 10 closest videos per idea."
        ),
        "",
    ]
    for idea, r in report.items():
        vids = sorted(r["videos"], key=lambda v: -v["views"])
        views = sorted(v["views"] for v in vids)
        median = views[len(views) // 2] if views else 0
        recent = sum(1 for v in vids if v["published"] >= "2025-10-23")
        lines += [
            f"## Idea {idea}: `{r['query']}`",
            "",
            (
                f"{len(vids)} results; median views {median:,}; {sum(v['views'] >= 100_000 for v in vids)} over 100k; "
                f"{recent} published in the last 12 months."
            ),
            "",
            "| Views | Views/day | Min | Published | Title | Channel |",
            "|---|---|---|---|---|---|",
        ]
        lines += [
            f"| {v['views']:,} | {v['views_per_day']:,} | {v['minutes']} | {v['published']} | "
            f"[{v['title'].replace('|', '/')}]({v['url']}) | {v['channel']} |"
            for v in vids[:6]
        ]
        lines.append("")
    (OUT / "competition.md").write_text("\n".join(lines))


if __name__ == "__main__":
    main()
