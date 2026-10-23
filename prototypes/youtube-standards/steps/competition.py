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
    4: "test oracle software testing",
    5: "LLM sycophancy code review",
    6: "LLM consistency testing same prompt",
    7: "heuristic test strategy model",
    8: "bug report writing safety language",
    9: "Copilot coding agent tests validation",
    10: "prompt injection testing OWASP LLM01",
    11: "excessive agency AI agent testing OWASP",
    12: "100% code coverage misleading",
    14: "LLM evals vs testing",
    15: "will AI replace software testers",
    16: "Post Office Horizon scandal software testing",
    17: "AI testing agent lessons learned",
    18: "self healing tests problems",
    19: "LLM evaluation framework architecture",
    20: "CI CD pipeline AI agents testing",
    21: "test strategy AI QA leaders",
    22: "manual tester career AI reskilling",
    23: "intermittent bug reproduce",
    24: "boundary value analysis",
}


def get(endpoint: str, **params: str) -> dict:
    params["key"] = os.environ["GOOGLE_CLOUD_API_KEY"]
    url = API + endpoint + "?" + urllib.parse.urlencode(params)
    try:
        return json.load(urllib.request.urlopen(url, timeout=60))
    except urllib.error.HTTPError as e:
        sys.exit(f"{endpoint}: {e.code} {e.read().decode()[:300]}")


ANCHORS = {  # every group needs at least one hit in the title or the first 400 characters of the description
    1: [["unit test"], ["ai", "copilot", "chatgpt", "llm"]],
    2: [["playwright"], ["agent", "healer", "mcp"]],
    3: [["cypress"], ["prompt", "self-heal", "self heal", "ai"]],
    4: [["oracle"], ["test"]],
    5: [["sycophan", "agree", "flatter", "yes-man"], ["llm", "ai", "chatgpt", "claude", "gpt"]],
    6: [["consisten", "determin", "same prompt", "variab"], ["llm", "chatgpt", "gpt", "model"]],
    7: [["heuristic", "test strategy"], ["test"]],
    8: [["bug report"], ["writ", "how to", "good"]],
    9: [["copilot"], ["agent"], ["test"]],
    10: [["prompt injection"], ["test", "owasp", "attack"]],
    11: [["excessive agency", "owasp"], ["agent", "llm"]],
    12: [["coverage"], ["test", "code"]],
    14: [["eval"], ["llm", "ai"]],
    15: [["replace"], ["tester", "qa", "testing"]],
    16: [["post office", "horizon"], ["software", "bug", "fujitsu", "it system"]],
    17: [["agent", "ai"], ["test"], ["lesson", "fail", "mistake", "learn", "wrong"]],
    18: [["self-heal", "self heal", "healing"], ["test"]],
    19: [["eval"], ["framework", "pipeline", "architect"], ["llm", "ai"]],
    20: [["ci/cd", "ci cd", "pipeline"], ["test"], ["ai", "agent", "llm"]],
    21: [["strategy"], ["test", "qa"], ["ai"]],
    22: [["manual test", "tester", "qa"], ["career", "reskill", "future", "job"], ["ai"]],
    23: [["reproduc", "intermittent", "flaky"], ["bug", "test", "issue"]],
    24: [["boundary value"], ["test", "analysis"]],
}


def relevant(idea: int, title: str, description: str) -> bool:
    text = (title + " " + description[:400]).lower()
    return all(any(term in text for term in group) for group in ANCHORS[idea])


def seconds(iso: str) -> int:
    m = re.fullmatch(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso)
    d, h, mi, s = (int(x or 0) for x in m.groups())
    return d * 86400 + h * 3600 + mi * 60 + s


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    now = datetime.now(UTC)
    report = {}
    for idea, q in QUERIES.items():
        cache = OUT / "raw" / f"{idea}.json"  # search quota is 100 calls a day: never search twice for the same query
        cached = json.loads(cache.read_text()) if cache.exists() else {}
        if cached.get("query") != q:
            found = get(
                "search", part="id", type="video", q=q, maxResults="25", relevanceLanguage="en", order="relevance"
            )
            cached = {"query": q, "ids": [i["id"]["videoId"] for i in found.get("items", [])]}
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text(json.dumps(cached))
        ids = cached["ids"]
        if not ids:
            report[idea] = {"query": q, "videos": []}
            continue
        vids = get("videos", part="snippet,statistics,contentDetails", id=",".join(ids))["items"]
        rows = []
        for v in vids:
            published = datetime.fromisoformat(v["snippet"]["publishedAt"])
            age = max((now - published).days, 1)
            views = int(v["statistics"].get("viewCount", 0))
            if not relevant(idea, v["snippet"]["title"], v["snippet"].get("description", "")):
                continue
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
            "Up to 25 results per idea, kept only when every anchor group matches the title or description start."
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
