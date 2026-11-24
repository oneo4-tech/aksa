"""Package a video's YouTube metadata: title, description, chapters, tags, and the published link.

Usage: uv run agentic/skills/content/package-video/scripts/package.py CHANNEL N [--video-url URL]

Reads, in the channel workspace's videos/<N>/:

  metadata.json        written by package-video: title, hook (the description's first line),
                       about (ABOUT sentences: what the video covers, and for whom), takeaways
                       (TAKEAWAYS lines: what the viewer takes away), chapters (a list of {scene, title}; empty for a Short), tags, hashtags,
                       paid_promotion (null, or the sponsor sentence), references (REFERENCES
                       key concepts as {concept, url}, such as {"concept": "Mutation testing",
                       "url": "https://pitest.org/"}, each url a citations.json source url or its
                       site root), and for a Short related, the number of its long-form video
  script.json          from write-video-script: type (long-form or short)
  render/scenes.json   from render.py: fps and per scene its frames; scenes play end to end,
                       so a chapter starts where its scene starts
  demo.json            from build-video-demo: link, the demo folder's link, and folder
  citations.json       from research-video: every claim verified (evidence.py)

and channel.yaml title_max and banned_phrases. It writes videos/<N>/description.md and
videos/<N>/packaging.json (title, description, chapters as {at, title}, tags, hashtags,
paid_promotion true or false, video_url, and for a Short related_video), the values the
owner pastes into YouTube Studio.

The description: the hook; the about paragraph, then "What you will take away:" with each
takeaway as a "- " line; for a long-form its chapters, for a Short "Full video: <URL>"
(the long-form's video_url from its packaging.json); "Code: <demo link>", then after a blank
line "AI kit: <demo link>/ai-kit", the rules, skill, and scripts build-video-demo puts there;
"References:" with each key concept and its link (per-claim sources stay in the demo README,
not the description); the disclosure lines (the synthetic narration voice,
and the paid promotion or "No paid promotion."); the hashtags, the first three most important,
since YouTube shows the first three above the title.

Refuses (exit 3), naming every problem at once: a blank title or hook, one over title_max, or a
banned phrase in the title, hook, about, a takeaway, or a chapter title; an about outside ABOUT
sentences; takeaways outside TAKEAWAYS lines, or one empty; a long-form's chapters not starting
at scene 1 (00:00), fewer than MIN_CHAPTERS, not ascending, naming a scene not rendered, or
shorter than MIN_CHAPTER_SECONDS; a Short with chapters, or whose long-form has no
video_url yet; references outside REFERENCES, or one whose url is not a citations.json
source url or that url's site root (scheme and host); tags outside TAGS; hashtags outside HASHTAGS (YouTube ignores them all past
fifteen), one not # and one word, or one repeated; angle brackets anywhere (YouTube rejects them); a description over DESCRIPTION_MAX
characters; demo.json without a link; citations missing or not all verified.

--video-url URL, once the video is published (a youtube.com/watch, youtube.com/shorts, or
youtu.be link): records it as video_url in packaging.json, which must exist, and, when
demo.json's folder is this video's (<N>-<slug>), fills that README's Video line in the local
demo clone with URL and rebuilds its Sources section from citations.json. A Short reusing
its long-form's demo folder leaves that README. It writes local files only: committing and
pushing the demo repository stay the owner's yes; nothing is uploaded to YouTube.

Exit codes: 0 written, 1 file error, 2 bad input (an invalid channel, a missing or invalid
metadata.json, script.json, or scenes.json, or an invalid URL), 3 refused.
"""

import argparse
import itertools
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

REPO_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO_ROOT / "agentic" / "scripts"))
# Formats are read through the scripts that write them: evidence.py the citations,
# scaffold.py the demo README.
sys.path.insert(0, str(REPO_ROOT / "agentic" / "skills" / "content" / "research-video" / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "agentic" / "skills" / "content" / "build-video-demo" / "scripts"))
import evidence
import scaffold
import youtube_channel

MIN_CHAPTERS = 3
MIN_CHAPTER_SECONDS = 10
TAGS = (5, 8)
HASHTAGS = (8, 15)
REFERENCES = (2, 5)
ABOUT = (2, 4)  # sentences of the about paragraph
TAKEAWAYS = (3, 5)  # lines the viewer takes away
TAKE_AWAY = "What you will take away:"
DESCRIPTION_MAX = 5000
VOICE = "Narration uses a synthetic AI voice."
MUSIC = "Music: an AI-generated ambient bed."
NO_PROMOTION = "No paid promotion."
HASHTAG = re.compile(r"#\w+")
VIDEO_ID = r"[A-Za-z0-9_-]{11}"
VIDEO_URL = re.compile(rf"https://(www\.)?youtube\.com/(watch\?v=|shorts/){VIDEO_ID}|https://youtu\.be/{VIDEO_ID}")
FIELDS = ["title", "hook", "about", "takeaways", "chapters", "tags", "hashtags", "paid_promotion", "references"]


class BadInput(Exception):
    """An invalid or missing input file, or an invalid URL: exit 2."""


class Refused(Exception):
    """Packaging that breaks a rule, or a step that must come first: exit 3."""


def read_json(path: Path, missing: str):
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        raise BadInput(f"{path}: missing; {missing}") from None
    except json.JSONDecodeError as error:
        raise BadInput(f"{path}: not valid JSON ({error})") from None


def metadata_problems(meta, kind: str) -> list[str]:
    """Missing or mistyped metadata.json fields: bad input, not a packaging rule."""
    if not isinstance(meta, dict):
        return ["must be a JSON object"]
    fields = FIELDS + (["related"] if kind == "short" else [])
    problems = [f"{field}: missing" for field in fields if field not in meta]
    texts = {"title": meta.get("title", ""), "hook": meta.get("hook", ""), "about": meta.get("about", "")}
    problems += [f"{field}: must be a string" for field, value in texts.items() if not isinstance(value, str)]
    for field in ["takeaways", "tags", "hashtags"]:
        value = meta.get(field, [])
        if not (isinstance(value, list) and all(isinstance(item, str) for item in value)):
            problems.append(f"{field}: must be a list of strings")
    chapters = meta.get("chapters", [])
    ok = isinstance(chapters, list) and all(
        isinstance(c, dict) and isinstance(c.get("scene"), int) and isinstance(c.get("title"), str) for c in chapters
    )
    if not ok:
        problems.append("chapters: must be a list of {scene: number, title: text}")
    references = meta.get("references", [])
    ok = isinstance(references, list) and all(
        isinstance(r, dict) and isinstance(r.get("concept"), str) and isinstance(r.get("url"), str) for r in references
    )
    if not ok:
        problems.append("references: must be a list of {concept, url}, the key concepts and their links")
    promotion = meta.get("paid_promotion")
    if promotion is not None and not (isinstance(promotion, str) and promotion.strip()):
        problems.append("paid_promotion: must be null or the sponsor sentence")
    if kind == "short" and "related" in meta and not isinstance(meta["related"], int):
        problems.append("related: must be the long-form video's issue number")
    return problems


def rendered_ok(rendered) -> bool:
    """Whether render.py's scenes.json has what chapters need: fps and each scene's number and frames."""
    if not isinstance(rendered, dict) or not isinstance(rendered.get("scenes"), list):
        return False
    fps_ok = isinstance(rendered.get("fps"), int | float) and rendered["fps"] > 0
    scene_ok = [
        isinstance(s, dict) and isinstance(s.get("scene"), int) and isinstance(s.get("frames"), int)
        for s in rendered["scenes"]
    ]
    return fps_ok and all(scene_ok)


def timestamp(seconds: float) -> str:
    whole = int(seconds)
    hours, rest = divmod(whole, 3600)
    minutes, secs = divmod(rest, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}" if hours else f"{minutes:02d}:{secs:02d}"


def chapter_times(chapters: list[dict], rendered: dict) -> tuple[list[dict], list[str]]:
    """Each chapter's start as {at, title}, and every chapter rule it breaks."""
    fps = rendered["fps"]
    starts, total = {}, 0.0
    for scene in rendered["scenes"]:
        starts[scene["scene"]] = total
        total += scene["frames"] / fps
    unknown = [c["scene"] for c in chapters if c["scene"] not in starts]
    problems = [f"chapters: scene {n} is not in render/scenes.json" for n in unknown]
    if len(chapters) < MIN_CHAPTERS:
        problems.append(f"chapters: {len(chapters)}, YouTube needs at least {MIN_CHAPTERS} chapters")
    if unknown or not chapters:
        return [], problems
    if chapters[0]["scene"] != min(starts):
        problems.append("chapters: the first chapter must start at 00:00, the first scene")
    times = [starts[c["scene"]] for c in chapters]
    if any(later <= earlier for earlier, later in itertools.pairwise(times)):
        problems.append("chapters: must be in ascending scene order, each scene once")
        return [], problems
    for chapter, start, end in zip(chapters, times, [*times[1:], total], strict=True):
        if end - start < MIN_CHAPTER_SECONDS:
            problems.append(f"chapters: '{chapter['title']}' is {end - start:g} s, each needs {MIN_CHAPTER_SECONDS} s")
    return [{"at": timestamp(t), "title": c["title"]} for c, t in zip(chapters, times, strict=True)], problems


def site_root(url: str) -> str:
    """A url's scheme and host with a trailing slash, such as https://www.satisfice.com/."""
    parts = urlsplit(url)
    return f"{parts.scheme}://{parts.netloc}/"


def reference_problems(references: list[dict], claims: list[dict]) -> list[str]:
    """Every rule the key-concept references break: their count, and links to pages the research cited."""
    problems = []
    if not REFERENCES[0] <= len(references) <= REFERENCES[1]:
        problems.append(f"references: {len(references)}, need {REFERENCES[0]} to {REFERENCES[1]} key concepts")
    allowed = {c["url"].rstrip("/") for c in claims} | {site_root(c["url"]).rstrip("/") for c in claims}
    for ref in references:
        if ref["url"].rstrip("/") not in allowed:
            problems.append(
                f"references: '{ref['concept']}' {ref['url']} is not a citations.json source page or its site root"
            )
    return problems


def package(meta: dict, kind: str, rendered: dict, demo, claims, related_url, config: dict) -> tuple[dict, list[str]]:
    """The packaging record, and every rule it breaks (pure)."""
    problems = []
    title = meta["title"]
    if not title.strip():
        problems.append("title: empty")
    elif not youtube_channel.title_ok(title, config):
        problems.append(f"title: over {config['title_max']} characters ({len(title)})")
    if not meta["hook"].strip():
        problems.append("hook: empty")
    about = meta["about"].strip()
    if not ABOUT[0] <= (count := len(re.findall(r"[^.!?]+[.!?]", about))) <= ABOUT[1]:
        problems.append(f"about: {count} sentences; need {ABOUT[0]} to {ABOUT[1]}: what the video covers, and for whom")
    takeaways = [line.strip() for line in meta["takeaways"]]
    if not TAKEAWAYS[0] <= len(takeaways) <= TAKEAWAYS[1]:
        problems.append(f"takeaways: {len(takeaways)}, need {TAKEAWAYS[0]} to {TAKEAWAYS[1]}")
    if not all(takeaways):
        problems.append("takeaways: a line is empty")
    named = [("title", title), ("hook", meta["hook"]), ("about", about)]
    named += [(f"takeaway '{line}'", line) for line in takeaways]
    named += [(f"chapter '{c['title']}'", c["title"]) for c in meta["chapters"]]
    for field, text in named:
        problems += [f"{field}: banned phrase '{p}'" for p in youtube_channel.banned_phrases(text, config)]
    if kind == "short":
        chapters = []
        if meta["chapters"]:
            problems.append("chapters: a Short has no chapters; leave the list empty")
        if not related_url:
            problems.append(
                f"related: long-form {meta['related']} has no video_url yet; once it is published, "
                f"run package.py <channel> {meta['related']} --video-url <URL>"
            )
    else:
        chapters, found = chapter_times(meta["chapters"], rendered)
        problems += found
    tags, hashtags = meta["tags"], meta["hashtags"]
    if not TAGS[0] <= len(tags) <= TAGS[1]:
        problems.append(f"tags: {len(tags)}, need {TAGS[0]} to {TAGS[1]}")
    if not HASHTAGS[0] <= len(hashtags) <= HASHTAGS[1]:
        problems.append(f"hashtags: {len(hashtags)}, need {HASHTAGS[0]} to {HASHTAGS[1]}")
    problems += [f"hashtag {tag!r}: must be # and one word" for tag in hashtags if not HASHTAG.fullmatch(tag)]
    seen = set()
    for tag in hashtags:
        if tag.lower() in seen:
            problems.append(f"hashtag {tag!r}: repeated")
        seen.add(tag.lower())
    link = demo.get("link") if isinstance(demo, dict) else None
    if not link:
        problems.append("demo.json: missing or without a link; build-video-demo writes it")
    if claims is None:
        problems.append("citations.json: missing; research-video writes it")
    else:
        problems += [f"citations: {p}" for p in evidence.gate_problems(claims)]
    if any(problem.startswith("citations") for problem in problems):
        claims = []
    else:
        problems += reference_problems(meta["references"], claims)

    promotion = meta["paid_promotion"]
    disclosure = (
        VOICE
        + "\n"
        + MUSIC
        + "\n"
        + (f"Includes paid promotion: {promotion.strip().rstrip('.')}." if promotion else NO_PROMOTION)
    )
    parts = [meta["hook"].strip(), about, "\n".join([TAKE_AWAY, *(f"- {line}" for line in takeaways)])]
    if kind == "short":
        parts.append(f"Full video: {related_url}")
    else:
        parts.append("\n".join(f"{c['at']} {c['title']}" for c in chapters))
    parts.append(f"Code: {link}")
    parts.append(f"AI kit: {link}/ai-kit")
    parts.append("References:\n" + "\n".join(f"- {r['concept']}: {r['url']}" for r in meta["references"]))
    parts.append(disclosure)
    if hashtags:
        parts.append(" ".join(hashtags))
    description = "\n\n".join(part for part in parts if part) + "\n"
    if len(description) > DESCRIPTION_MAX:
        problems.append(f"description: over {DESCRIPTION_MAX} characters ({len(description)})")
    if any(ch in text for ch in "<>" for text in [title, description, *tags]):
        problems.append("angle brackets: YouTube rejects < and > in the title, description, and tags")
    record = {
        "type": kind,
        "title": title,
        "description": description,
        "chapters": chapters,
        "tags": tags,
        "hashtags": hashtags,
        "paid_promotion": bool(promotion),
        "video_url": None,
    }
    if kind == "short":
        record["related_video"] = related_url
    return record, problems


def optional_json(path: Path):
    """A file's JSON, or None when it is missing; refused when it is not valid JSON."""
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        return None
    except json.JSONDecodeError as error:
        raise Refused(f"{path}: not valid JSON ({error})") from None


def build(channel: youtube_channel.Channel, number: int) -> Path:
    """Write packaging.json and description.md; return the video folder."""
    video = channel.workspace / "videos" / str(number)
    script = read_json(video / "script.json", "write-video-script writes it")
    kind = script.get("type") if isinstance(script, dict) else None
    if kind not in ("long-form", "short"):
        raise BadInput(f"{video / 'script.json'}: type must be long-form or short")
    meta = read_json(video / "metadata.json", "package-video writes it")
    if problems := metadata_problems(meta, kind):
        raise BadInput(f"{video / 'metadata.json'}:\n  " + "\n  ".join(problems))
    rendered = read_json(video / "render" / "scenes.json", "render the video first (render.py)")
    if not rendered_ok(rendered):
        raise BadInput(f"{video / 'render' / 'scenes.json'}: needs fps and scenes with scene and frames; run render.py")
    related_url = None
    if kind == "short":
        related = optional_json(channel.workspace / "videos" / str(meta["related"]) / "packaging.json")
        related_url = related.get("video_url") if isinstance(related, dict) else None
    demo = optional_json(video / "demo.json")
    claims = optional_json(video / "citations.json")
    record, problems = package(meta, kind, rendered, demo, claims, related_url, channel.config)
    if problems:
        raise Refused(f"{video}:\n  " + "\n  ".join(problems))
    previous = optional_json(video / "packaging.json")
    if isinstance(previous, dict):
        record["video_url"] = previous.get("video_url")
    (video / "description.md").write_text(record["description"])
    (video / "packaging.json").write_text(json.dumps(record, indent=1) + "\n")
    return video


def publish(channel: youtube_channel.Channel, number: int, url: str, root: Path) -> tuple[Path, Path | None]:
    """Record url in packaging.json and fill this video's demo README; return both paths."""
    if not VIDEO_URL.fullmatch(url):
        raise BadInput(
            f"{url!r} is not a YouTube video link (https://www.youtube.com/watch?v=..., /shorts/..., youtu.be/...)"
        )
    video = channel.workspace / "videos" / str(number)
    record = optional_json(video / "packaging.json")
    if not isinstance(record, dict):
        raise Refused(f"{video / 'packaging.json'}: missing; package the video first (run without --video-url)")
    demo = optional_json(video / "demo.json") or {}
    readme = None
    if str(demo.get("folder", "")).startswith(f"{number}-"):
        readme = root / ".projects" / "content" / channel.config["demos"]["path"] / demo["folder"] / "README.md"
        if not readme.is_file():
            raise Refused(f"{readme.relative_to(root)}: missing; build-video-demo scaffolds it")
        claims = optional_json(video / "citations.json")
        if claims is None or evidence.gate_problems(claims):
            raise Refused(f"{video / 'citations.json'}: missing or not all verified; run evidence.py")
        text = scaffold.with_video(readme.read_text(), url, claims)
    record["video_url"] = url
    (video / "packaging.json").write_text(json.dumps(record, indent=1) + "\n")
    if readme:
        readme.write_text(text)
    return video / "packaging.json", readme


def main(argv: list[str] | None = None, root: Path = REPO_ROOT) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("channel")
    parser.add_argument("number", type=int, help="the video's content issue number")
    parser.add_argument("--video-url", help="the published video's link, to record and put in the demo README")
    args = parser.parse_args(argv)
    try:
        channel = youtube_channel.load(args.channel, root)
        if args.video_url:
            packaging, readme = publish(channel, args.number, args.video_url, root)
            print(f"recorded: {packaging.relative_to(root)} video_url {args.video_url}")
            print(
                f"readme: {readme.relative_to(root)}" if readme else "readme: not this video's demo folder; left as is"
            )
        else:
            video = build(channel, args.number)
            print(
                f"written: {(video / 'packaging.json').relative_to(root)}, {(video / 'description.md').relative_to(root)}"
            )
    except (youtube_channel.ChannelError, BadInput) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    except (Refused, scaffold.Refused) as error:
        print(f"refused: {error}", file=sys.stderr)
        return 3
    except OSError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
