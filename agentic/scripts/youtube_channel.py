"""Load a YouTube channel's settings and style guide, and set up its workspace.

Usage: uv run agentic/scripts/youtube_channel.py COMMAND CHANNEL

  check CHANNEL   load the channel and report ok, or every missing or invalid field
  init CHANNEL    make the workspace a git repository that ignores generated media,
                  with a videos/ folder; safe to run again

A channel's workspace is .projects/content/yt-<channel>/, reached through the
repo-root .projects link (D-012). It holds two files the owner writes:

channel.yaml, the machine values every content script reads:

  name: Example Lab                      # display name
  url: https://...                       # channel URL; never in a tracked component
  voice: {id: Puck, style: "warm and conversational", pace: 0.92}
  palette: {background: "#000000", syntax: "#FF3B3B", name: "#FFFFFF", suffix: "#00E5FF"}
  loudness: {lufs: -14, true_peak: -1}   # loudness target, LUFS and dBTP
  music_db: -24                          # music bed level, dB
  cadence: {long_form_per_week: 1, shorts_per_week: 2, owner_hours_per_week: 5}
                                         # weekly uploads; the owner-hours budget for them
  labels: {channel: "channel:example-lab"}
  pronunciation: {pytest: "pie test"}    # word -> spoken respelling; may be empty
  banned_phrases: ["in this video"]      # may be empty
  title_max: 60                          # longest title, characters
  demos: {repo: example-org/example-demos, path: example-demos}
                                         # the public demo repository (owner/name) and its
                                         # local clone, a folder of .projects/content/ that is
                                         # not a channel workspace (yt-*)

style-guide.md, the human rules every specialist reads, with one "## " section per
heading in SECTIONS, spelled exactly.

Content scripts import load(channel) and the pure writing checks banned_phrases(text, config)
(whole words, any case) and title_ok(title, config) (at most title_max characters).

Media (video, audio, images) is gitignored in the workspace; text artifacts and
SVG branding sources stay trackable.

Exit codes: 0 done, 1 git or file error, 2 bad input or an invalid channel.
"""

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]

SECTIONS = [
    "Voice",
    "Writing rules",
    "Visual style",
    "Slides and animation",
    "Screen capture",
    "Audio",
    "Captions",
    "Thumbnails",
    "Metadata",
    "Shorts",
    "Gate 1 checklist",
    "Gate 2 checklist",
    "Gate 3 checklist",
]
MEDIA = ["mp4", "mov", "webm", "wav", "mp3", "m4a", "png", "jpg", "jpeg", "gif", "webp"]
GITIGNORE = ["# Generated media stays out of git; only text artifacts are committed."] + [f"*.{ext}" for ext in MEDIA]

NAME = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")
REPO = re.compile(r"[A-Za-z0-9-]+/[A-Za-z0-9._-]+")
COLOUR = re.compile(r"#[0-9A-Fa-f]{6}")
HEADING = re.compile(r"^## (.+?)\s*$", re.MULTILINE)


class ChannelError(Exception):
    """A missing or invalid channel: exit 2."""


@dataclass
class Channel:
    name: str
    workspace: Path
    config: dict
    style: dict[str, str]  # section heading -> its text


def _number(value) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def _text(value) -> str | None:
    return None if isinstance(value, str) and value.strip() else "must be a non-empty string"


def _url(value) -> str | None:
    return None if isinstance(value, str) and value.startswith("https://") else "must be an https:// URL"


def _colour(value) -> str | None:
    return None if isinstance(value, str) and COLOUR.fullmatch(value) else "must be a colour like #1A2B3C"


def _num(value) -> str | None:
    return None if _number(value) else "must be a number"


def _positive(value) -> str | None:
    return None if _number(value) and value > 0 else "must be a number above 0"


def _count(value) -> str | None:
    ok = isinstance(value, int) and not isinstance(value, bool) and value >= 0
    return None if ok else "must be a whole number, 0 or more"


def _length(value) -> str | None:
    ok = isinstance(value, int) and not isinstance(value, bool) and value > 0
    return None if ok else "must be a whole number above 0"


def _label(value) -> str | None:
    ok = isinstance(value, str) and value.startswith("channel:") and NAME.fullmatch(value.removeprefix("channel:"))
    return None if ok else "must be a label like channel:<name>"


def _words(value) -> str | None:
    ok = isinstance(value, dict) and all(isinstance(k, str) and isinstance(v, str) for k, v in value.items())
    return None if ok else "must map each word to its spoken form"


def _repo(value) -> str | None:
    return None if isinstance(value, str) and REPO.fullmatch(value) else "must be a GitHub repository like owner/name"


def _folder(value) -> str | None:
    ok = isinstance(value, str) and NAME.fullmatch(value) and not value.startswith("yt-")
    return None if ok else "must be one lowercase hyphenated folder name of .projects/content/, not yt-*"


def _phrases(value) -> str | None:
    return None if isinstance(value, list) and all(isinstance(p, str) for p in value) else "must be a list of strings"


# Field -> its check, or a nested mapping of fields.
SCHEMA: dict = {
    "name": _text,
    "url": _url,
    "voice": {"id": _text, "style": _text, "pace": _positive},
    "palette": {"background": _colour, "syntax": _colour, "name": _colour, "suffix": _colour},
    "loudness": {"lufs": _num, "true_peak": _num},
    "music_db": _num,
    "cadence": {"long_form_per_week": _count, "shorts_per_week": _count, "owner_hours_per_week": _positive},
    "labels": {"channel": _label},
    "pronunciation": _words,
    "banned_phrases": _phrases,
    "title_max": _length,
    "demos": {"repo": _repo, "path": _folder},
}


def config_problems(data, schema: dict = SCHEMA, prefix: str = "") -> list[str]:
    """Every missing or invalid field of data against schema, as 'field: problem'."""
    problems = []
    for key, rule in schema.items():
        field = prefix + key
        if not isinstance(data, dict) or key not in data:
            problems.append(f"{field}: missing")
        elif isinstance(rule, dict):
            if isinstance(data[key], dict):
                problems += config_problems(data[key], rule, field + ".")
            else:
                problems.append(f"{field}: must be a mapping of {', '.join(rule)}")
        elif problem := rule(data[key]):
            problems.append(f"{field}: {problem}")
    return problems


def style_sections(text: str) -> dict[str, str]:
    """Second-level heading -> the text under it, up to the next such heading."""
    parts = HEADING.split(text)
    return {parts[i]: parts[i + 1].strip() for i in range(1, len(parts) - 1, 2)}


def _plain(text: str) -> str:
    """Curly apostrophes as straight ones, so "let’s" matches "let's"."""
    return text.replace("\u2019", "'").replace("\u2018", "'")


def banned_phrases(text: str, config: dict) -> list[str]:
    """The channel's banned phrases in text, as listed in config: whole words, any case or spacing."""
    text = _plain(text)
    found = []
    for phrase in config["banned_phrases"]:
        words = r"\s+".join(re.escape(word) for word in _plain(phrase).split())
        if words and re.search(rf"(?<!\w){words}(?!\w)", text, re.IGNORECASE):
            found.append(phrase)
    return found


def title_ok(title: str, config: dict) -> bool:
    """Whether title is non-blank and at most the channel's title_max characters."""
    return bool(title.strip()) and len(title) <= config["title_max"]


def workspace(channel: str, root: Path = REPO_ROOT) -> Path:
    if not NAME.fullmatch(channel):
        raise ChannelError(f"channel name {channel!r} must be lowercase words joined by hyphens, such as testlab")
    return root / ".projects" / "content" / f"yt-{channel}"


def load(channel: str, root: Path = REPO_ROOT) -> Channel:
    """The channel's settings and style guide. Raises ChannelError naming every problem."""
    path = workspace(channel, root)
    problems = []
    config = None
    try:
        config = yaml.safe_load((path / "channel.yaml").read_text())
        problems += [f"channel.yaml: {p}" for p in config_problems(config)]
    except FileNotFoundError:
        problems.append("channel.yaml: missing")
    except yaml.YAMLError as error:
        problems.append(f"channel.yaml: not valid YAML ({error})")
    style: dict[str, str] = {}
    try:
        style = style_sections((path / "style-guide.md").read_text())
    except FileNotFoundError:
        problems.append("style-guide.md: missing; every channel needs one")
    else:
        problems += [f"style-guide.md: section '## {s}' missing" for s in SECTIONS if s not in style]
    if problems:
        raise ChannelError(f"channel {channel} at {path.relative_to(root)}:\n  " + "\n  ".join(problems))
    return Channel(channel, path, config, style)


def init(channel: str, root: Path = REPO_ROOT) -> Path:
    """Make the workspace a git repository that ignores media, with videos/. Idempotent."""
    path = workspace(channel, root)
    if not (root / ".projects").is_dir():
        raise ChannelError(".projects is missing; run uv run agentic/scripts/link_external.py first")
    (path / "videos").mkdir(parents=True, exist_ok=True)
    if not (path / ".git").exists():
        # A git hook exports GIT_DIR and friends; without this, init would reinitialise that repository.
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        subprocess.run(["git", "init", "--quiet", str(path)], check=True, env=env)
    gitignore = path / ".gitignore"
    lines = gitignore.read_text().splitlines() if gitignore.exists() else []
    missing = [line for line in GITIGNORE if line not in lines]
    if missing:
        gitignore.write_text("\n".join(lines + missing) + "\n")
    return path


def main(argv: list[str] | None = None, root: Path = REPO_ROOT) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["check", "init"])
    parser.add_argument("channel")
    args = parser.parse_args(argv)
    try:
        if args.command == "check":
            channel = load(args.channel, root)
            print(f"ok: {args.channel} ({channel.workspace.relative_to(root)})")
        else:
            path = init(args.channel, root)
            print(f"ready: {path.relative_to(root)}")
    except ChannelError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    except (OSError, subprocess.CalledProcessError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
