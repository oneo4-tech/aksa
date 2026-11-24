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
  narration_avoid_names: ["Jane Doe"]    # optional: people narration never names (authors, researchers,
                                         # creators); the description's References credit them
  title_max: 60                          # longest title, characters
  demos: {repo: example-org/example-demos, path: example-demos}
                                         # the public demo repository (owner/name) and its
                                         # local clone, a folder of .projects/content/ that is
                                         # not a channel workspace (yt-*)
  thumbnail: {art_style: "3D clay render, soft studio lighting", field: ["#4A4A4A", "#262626"]}
                                         # the style every thumbnail's art is asked in; field,
                                         # optional, the two colours of the thumbnail's background
                                         # gradient (design-thumbnail's default when absent)
  branding: {wordmarks: [examplelab], tagline: "One line on the banner", subline: "a smaller second line"}
                                         # suffix words of the <oneo4/>word wordmarks made, the
                                         # first on the banner, with the banner's two text lines;
                                         # backdrop_prompt, optional, the image brand-channel
                                         # --backdrop asks for (its default when absent)
  background: {image: branding/backdrop.jpg, opacity: 0.3, fit: cover}
                                         # optional: an image of the workspace shown behind every
                                         # rendered scene; fit, optional, cover (filling the frame,
                                         # such as brand-channel's backdrop) or contain (centred,
                                         # such as a wordmark; the default); opacity above 0 and at
                                         # most BACKGROUND_OPACITY for its fit (0.35 cover, 0.15
                                         # contain)

A field marked optional may be absent; when present it is checked like the others.

style-guide.md, the human rules every specialist reads, with one "## " section per
heading in SECTIONS, spelled exactly.

Content scripts import load(channel) and the pure writing checks banned_phrases(text, config)
(whole words, any case), phrases_in(text, phrases) (the same match for any list, such as
narration_avoid_names), and title_ok(title, config) (at most title_max characters).

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
SUFFIX = re.compile(r"[a-z]+")
HEADING = re.compile(r"^## (.+?)\s*$", re.MULTILINE)
# The most a background image may show, by fit: a centred image (contain) stays faint; a dim photo-like backdrop
# filling the frame (cover) may show more, its own darkness keeping text contrast; never competing with the scene.
BACKGROUND_OPACITY = {"contain": 0.15, "cover": 0.35}
BACKGROUND_FIT = "contain"  # when fit is absent


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


def _suffixes(value) -> str | None:
    ok = isinstance(value, list) and value and all(isinstance(w, str) and SUFFIX.fullmatch(w) for w in value)
    return None if ok else "must be a non-empty list of lowercase words, such as [testlab]"


def _colours(value) -> str | None:
    ok = isinstance(value, list) and len(value) == 2 and all(isinstance(c, str) and COLOUR.fullmatch(c) for c in value)
    return None if ok else "must be two colours like [#4A4A4A, #262626]"


IMAGE_TYPES = (".svg", ".png", ".jpg", ".jpeg")  # the background image types render-video embeds


def _image(value) -> str | None:
    ok = isinstance(value, str) and value.strip() and not value.startswith("/") and ".." not in Path(value).parts
    ok = ok and Path(value).suffix.lower() in IMAGE_TYPES
    return (
        None
        if ok
        else f"must be an image ({', '.join(IMAGE_TYPES)}) inside the workspace, such as branding/wordmark.svg"
    )


def _opacity(value) -> str | None:
    """Above 0; its limit depends on fit, so background_problems checks it."""
    limits = " or ".join(f"{limit} (fit {fit})" for fit, limit in BACKGROUND_OPACITY.items())
    return None if _positive(value) is None else f"must be a number above 0 and at most {limits}"


def _fit(value) -> str | None:
    return None if value in BACKGROUND_OPACITY else f"must be {' or '.join(BACKGROUND_OPACITY)}"


def _phrases(value) -> str | None:
    return None if isinstance(value, list) and all(isinstance(p, str) for p in value) else "must be a list of strings"


@dataclass
class Optional:
    """A field that may be absent: its check, or nested mapping, applies only when present."""

    rule: object


# Field -> its check, or a nested mapping of fields; Optional(...) for a field that may be absent.
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
    "narration_avoid_names": Optional(_phrases),
    "title_max": _length,
    "demos": {"repo": _repo, "path": _folder},
    "thumbnail": {"art_style": _text, "field": Optional(_colours)},
    "branding": {"wordmarks": _suffixes, "tagline": _text, "subline": _text, "backdrop_prompt": Optional(_text)},
    "background": Optional({"image": _image, "opacity": _opacity, "fit": Optional(_fit)}),
}


def config_problems(data, schema: dict = SCHEMA, prefix: str = "") -> list[str]:
    """Every missing or invalid field of data against schema, as 'field: problem'."""
    problems = []
    for key, rule in schema.items():
        field = prefix + key
        optional = isinstance(rule, Optional)
        rule = rule.rule if optional else rule
        if optional and isinstance(data, dict) and key not in data:
            continue
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


def background_problems(config, path: Path) -> list[str]:
    """The optional background, once its fields are valid: its image a file of the workspace at path, and its
    opacity at most its fit's limit."""
    background = config.get("background") if isinstance(config, dict) else None
    if not isinstance(background, dict):
        return []
    problems = []
    image, opacity = background.get("image"), background.get("opacity")
    fit = background.get("fit", BACKGROUND_FIT)
    if image is not None and not _image(image) and not (path / image).is_file():
        problems.append(
            f"background.image: {image} is not a file in the workspace; brand-channel makes the channel's branding"
        )
    if not _fit(fit) and not _opacity(opacity) and opacity > (limit := BACKGROUND_OPACITY[fit]):
        problems.append(f"background.opacity: must be a number above 0 and at most {limit} for fit {fit}")
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
    return phrases_in(text, config["banned_phrases"])


def phrases_in(text: str, phrases: list[str]) -> list[str]:
    """Each of phrases found in text, as listed: whole words, any case or spacing."""
    text = _plain(text)
    found = []
    for phrase in phrases:
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
        problems += [f"channel.yaml: {p}" for p in background_problems(config, path)]
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
