"""Score a video idea card and add the closest existing YouTube videos to it.

Usage: uv run agentic/skills/content/scan-video-ideas/scripts/competition.py CHANNEL CARD [--top N]

CARD is an idea card, a JSON file with these fields (REQUIRED):

  title            the working title, challenge style
  pillar           the channel pillar it serves
  rst_concept      the Rapid Software Testing concept it applies
  claim            the mainstream claim it examines
  tester_question  the question a tester asks that the mainstream take skips
  proof            what the demo shows on screen
  format           long-form or short
  hook             the freshness hook and its date, or "evergreen"
  sources          https links backing the card, at least one
  risks            rights, real-people, or accuracy risks, at least one
  scores           1-5 for each factor in WEIGHTS
  query            the YouTube search for competing videos
  anchors          term groups, such as [["unit test"], ["ai", "llm"]]: a video is relevant
                   when each group has a term starting a word in its title or the first
                   400 characters of its description

It prints JSON (score, the closest relevant videos in search order with views,
views per day, minutes, published date, title, channel, and url) and writes the
card as Markdown next to CARD (CARD with .md), the brief for content_issue.py new.

YouTube Data API v3: search.list (type video) then videos.list (statistics and
duration), with the API key in the GOOGLE_CLOUD_API_KEY environment variable, read
from .env by uv run --env-file .env. The search quota is 100 calls a day, so each
query's results are cached in the channel workspace, one file per exact query,
research/competition-cache/<query slug>-<query hash>.json, and a query cached
today calls YouTube no more; the key is needed only for a query not cached today.

Exit codes: 0 done, 1 YouTube or file error, 2 bad input (an invalid card or
channel, or the key missing).
"""

import argparse
import datetime
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO_ROOT / "agentic" / "scripts"))
import youtube_channel

API = "https://www.googleapis.com/youtube/v3/"
KEY_VARIABLE = "GOOGLE_CLOUD_API_KEY"
CACHE = Path("research") / "competition-cache"
SEARCH_RESULTS = 25
DESCRIPTION_START = 400
FORMATS = ["long-form", "short"]

# Factor -> weight. Each factor is scored 1-5; ideas under PARK stay parked.
WEIGHTS = {"lens": 3, "proof": 3, "freshness": 2, "audience_pull": 2, "distinctness": 2, "effort": 1}
MAX_SCORE = 5 * sum(WEIGHTS.values())
PARK = 40

TEXT = ["title", "pillar", "rst_concept", "claim", "tester_question", "proof", "hook", "query"]
REQUIRED = TEXT + ["format", "sources", "risks", "scores", "anchors"]

Http = Callable[[str, dict], dict]


class BadInput(Exception):
    """An invalid card or channel, or the key missing: exit 2."""


class ApiError(Exception):
    """YouTube refused or failed a call: exit 1."""


def _strings(value) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(v, str) and v.strip() for v in value)


def card_problems(card) -> list[str]:
    """Every missing or invalid field of an idea card, as 'field: problem'."""
    if not isinstance(card, dict):
        return ["card: must be a JSON object"]
    problems = [f"{field}: missing" for field in REQUIRED if field not in card]
    for field in TEXT:
        if field in card and not (isinstance(card[field], str) and card[field].strip()):
            problems.append(f"{field}: must be a non-empty string")
    if "format" in card and card["format"] not in FORMATS:
        problems.append(f"format: must be one of {', '.join(FORMATS)}")
    if "sources" in card and not (_strings(card["sources"]) and all(s.startswith("https://") for s in card["sources"])):
        problems.append("sources: must be a list of https:// links, at least one")
    if "risks" in card and not _strings(card["risks"]):
        problems.append("risks: must be a list of risks, at least one")
    if "anchors" in card and not (
        isinstance(card["anchors"], list) and card["anchors"] and all(map(_strings, card["anchors"]))
    ):
        problems.append("anchors: must be a list of term groups, each a non-empty list of terms")
    if "scores" in card:
        scores = card["scores"]
        if not isinstance(scores, dict):
            problems.append(f"scores: must map {', '.join(WEIGHTS)} to 1-5")
        else:
            for factor in WEIGHTS:
                value = scores.get(factor)
                if not (isinstance(value, int) and not isinstance(value, bool) and 1 <= value <= 5):
                    problems.append(f"scores.{factor}: must be a whole number 1-5")
    return problems


def score(scores: dict) -> dict:
    total = sum(WEIGHTS[factor] * scores[factor] for factor in WEIGHTS)
    return {"total": total, "max": MAX_SCORE, "parked": total < PARK}


def relevant(anchors: list[list[str]], title: str, description: str) -> bool:
    """Each anchor group has a term starting a word in the title or the description start."""
    text = (title + " " + description[:DESCRIPTION_START]).lower()
    return all(any(re.search(r"\b" + re.escape(term.lower()), text) for term in group) for group in anchors)


def seconds(duration: str) -> int:
    """An ISO 8601 duration, such as PT1H2M3S, in seconds."""
    match = re.fullmatch(r"P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?", duration)
    if not match:
        raise ApiError(f"videos: unreadable duration {duration!r}")
    days, hours, minutes, secs = (int(x or 0) for x in match.groups())
    return ((days * 24 + hours) * 60 + minutes) * 60 + secs


def video_row(video: dict, today: datetime.date) -> dict:
    published = datetime.date.fromisoformat(video["published"])
    return {
        "title": video["title"],
        "channel": video["channel"],
        "url": f"https://www.youtube.com/watch?v={video['id']}",
        "published": video["published"],
        "views": video["views"],
        "views_per_day": round(video["views"] / max((today - published).days, 1), 1),
        "minutes": round(video["seconds"] / 60, 1),
    }


def closest(videos: list[dict], anchors: list[list[str]], today: datetime.date, top: int) -> list[dict]:
    """The first top relevant videos, in search order (closest first)."""
    kept = [v for v in videos if relevant(anchors, v["title"], v["description"])]
    return [video_row(v, today) for v in kept[:top]]


def slug(query: str) -> str:
    """A readable file name, with a hash of the exact query so no two queries share one."""
    readable = re.sub(r"[^a-z0-9]+", "-", query.lower()).strip("-")[:80] or "query"
    return f"{readable}-{hashlib.sha256(query.encode()).hexdigest()[:10]}"


def markdown(card: dict, result: dict) -> str:
    s = result["score"]
    lines = [
        f"# {card['title']}",
        "",
        "| Field | Value |",
        "|---|---|",
        *(
            f"| {label} | {str(card[field]).replace('|', '/')} |"
            for label, field in [
                ("Pillar", "pillar"),
                ("RST concept", "rst_concept"),
                ("Claim", "claim"),
                ("Tester's question", "tester_question"),
                ("Proof", "proof"),
                ("Format", "format"),
                ("Hook", "hook"),
            ]
        ),
        "",
        "## Sources",
        "",
        *(f"- {source}" for source in card["sources"]),
        "",
        "## Risks",
        "",
        *(f"- {risk}" for risk in card["risks"]),
        "",
        "## Score",
        "",
        "| Factor | Weight | Score | Points |",
        "|---|---|---|---|",
        *(f"| {f} | {w} | {card['scores'][f]} | {w * card['scores'][f]} |" for f, w in WEIGHTS.items()),
        "",
        f"Total {s['total']} / {s['max']}{', parked (under ' + str(PARK) + ')' if s['parked'] else ''}.",
        "",
        "## Closest YouTube videos",
        "",
        f"Search `{result['query']}` on {result['searched']}, kept when every anchor group matches.",
        "",
    ]
    if result["videos"]:
        lines += ["| Views | Views/day | Min | Published | Title | Channel |", "|---|---|---|---|---|---|"]
        lines += [
            f"| {v['views']:,} | {v['views_per_day']:,} | {v['minutes']} | {v['published']} | "
            f"[{v['title'].replace('|', '/')}]({v['url']}) | {v['channel'].replace('|', '/')} |"
            for v in result["videos"]
        ]
    else:
        lines.append("No relevant videos found.")
    return "\n".join(lines) + "\n"


# Thin shell: YouTube, the cache file, and the card files.


def fetch(endpoint: str, params: dict) -> dict:
    """One YouTube Data API call. Errors never include the URL, which holds the key."""
    request = urllib.request.Request(API + endpoint + "?" + urllib.parse.urlencode(params))
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        try:
            message = json.loads(error.read())["error"]["message"]
        except (ValueError, KeyError, TypeError):
            message = error.reason
        raise ApiError(f"{endpoint}: HTTP {error.code}: {message}") from None
    except (urllib.error.URLError, TimeoutError) as error:
        raise ApiError(f"{endpoint}: {getattr(error, 'reason', error)}") from None


def search(query: str, http: Http) -> list[dict]:
    """The query's videos in search order, with what the card needs from each."""
    key = os.environ.get(KEY_VARIABLE)
    if not key:
        raise BadInput(
            f"{KEY_VARIABLE} is not set: put a Google Cloud API key with the YouTube Data API enabled "
            "in .env and run with uv run --env-file .env"
        )
    found = http(
        "search",
        {
            "part": "id",
            "type": "video",
            "q": query,
            "maxResults": str(SEARCH_RESULTS),
            "relevanceLanguage": "en",
            "key": key,
        },
    )
    ids = [item["id"]["videoId"] for item in found.get("items", [])]
    if not ids:
        return []
    details = http("videos", {"part": "snippet,statistics,contentDetails", "id": ",".join(ids), "key": key})
    by_id = {item["id"]: item for item in details.get("items", [])}
    return [
        {
            "id": video_id,
            "title": item["snippet"]["title"],
            "channel": item["snippet"]["channelTitle"],
            "description": item["snippet"].get("description", "")[:DESCRIPTION_START],
            "published": item["snippet"]["publishedAt"][:10],
            "views": int(item["statistics"].get("viewCount", 0)),
            "seconds": seconds(item["contentDetails"]["duration"]),
        }
        for video_id in ids
        if (item := by_id.get(video_id))
    ]


def cached_search(query: str, folder: Path, http: Http, today: datetime.date) -> list[dict]:
    """The query's videos from today's cache, else from YouTube, then cached."""
    path = folder / f"{slug(query)}.json"
    if path.exists():
        try:
            cached = json.loads(path.read_text())
        except json.JSONDecodeError:
            raise BadInput(f"{path}: unreadable cache; check today's searches are spent before deleting it") from None
        if cached.get("query") == query and cached.get("date") == today.isoformat():
            return cached["videos"]
    videos = search(query, http)
    folder.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"query": query, "date": today.isoformat(), "videos": videos}, indent=1) + "\n")
    return videos


def read_card(path: Path) -> dict:
    try:
        card = json.loads(path.read_text())
    except FileNotFoundError:
        raise BadInput(f"{path}: no such card") from None
    except json.JSONDecodeError as error:
        raise BadInput(f"{path}: not valid JSON ({error})") from None
    if problems := card_problems(card):
        raise BadInput(f"idea card {path}:\n  " + "\n  ".join(problems))
    return card


def main(
    argv: list[str] | None = None,
    http: Http = fetch,
    root: Path = REPO_ROOT,
    today: datetime.date | None = None,
) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("channel")
    parser.add_argument("card", type=Path)
    parser.add_argument("--top", type=int, default=6, help="most videos to list (default 6)")
    args = parser.parse_args(argv)
    today = today or datetime.date.today()
    try:
        card = read_card(args.card)
        workspace = youtube_channel.load(args.channel, root).workspace
        videos = cached_search(card["query"], workspace / CACHE, http, today)
        result = {
            "title": card["title"],
            "score": score(card["scores"]),
            "query": card["query"],
            "searched": today.isoformat(),
            "videos": closest(videos, card["anchors"], today, args.top),
        }
        args.card.with_suffix(".md").write_text(markdown(card, result))
    except (BadInput, youtube_channel.ChannelError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    except (ApiError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
