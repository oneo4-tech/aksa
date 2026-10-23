"""Create a video's demo folder in the channel's local clone of its public demo repository.

Usage: uv run agentic/skills/content/build-video-demo/scripts/scaffold.py CHANNEL N --slug SLUG --proves TEXT

Reads channel.yaml's demos: {repo, path}: the public repository (owner/name) and its local
clone at .projects/content/<path>/, and the video's verified citations, videos/<N>/citations.json
from research-video. Creates <clone>/<N>-<SLUG>/ with:

  README.md    title (the content issue's), what it proves (TEXT), how to run, a Video section
               (the line VIDEO_PENDING, which package-video fills with the published video's
               link, the channel's link from channel.yaml url, and the folder's own link) and
               a Sources section (each claim, its quoted line, and its text-fragment link),
               and the MIT note; never a link to the content issue, whose tracker is private
  demo/        the code the video shows (empty, with .gitkeep)
  tests/       the tests that prove the claim (empty, with .gitkeep)
  demo.tape    the VHS tape recording the terminal demo, from references/demo.tape
  .gitignore   the recorded media, which stays out of git

and prints the folder, then the description link https://github.com/<repo>/tree/main/<N>-<SLUG>.

It refuses (exit 3) a folder that already exists, a clone that is missing or not a git
repository, a repository that does not exist on GitHub (the owner creates it once and clones
it), and citations missing or not all verified (research-video's evidence.py). It only reads GitHub; it never creates a repository, commits, or pushes.

Exit codes: 0 created, 1 a GitHub or file error, 2 bad input (an invalid channel, slug, or an
issue that is not this channel's), 3 refused.
"""

import argparse
import json
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO_ROOT / "agentic" / "scripts"))
# The citations format is read through the script that writes it, research-video's evidence.py.
sys.path.insert(0, str(REPO_ROOT / "agentic" / "skills" / "content" / "research-video" / "scripts"))
import evidence
import github_issues
import youtube_channel

MEDIA_IGNORE = "# Recorded media stays out of git.\n*.mp4\n*.gif\n*.webm\n"
VIDEO_LINE = "- Video: "
VIDEO_PENDING = VIDEO_LINE + "not published yet"
SOURCES = "## Sources"
SOURCES_INTRO = "The video's claims, each with the line quoted from its source; each link opens the page at that line."


class BadInput(Exception):
    """An invalid slug or an issue of another channel: exit 2."""


class Refused(Exception):
    """A step the owner or the skill must take first: exit 3."""


class GitHub(github_issues.GitHub):
    """The read-only gh calls scaffold.py needs; tests replace it with a fake."""

    def repo_exists(self, repo: str) -> bool:
        try:
            self._gh("repo", "view", repo, "--json", "name")
        except github_issues.GitHubError as error:
            if "Could not resolve to a Repository" in str(error):
                return False
            raise
        return True

    def issue_link(self, number: int) -> dict:
        data = json.loads(self._gh("issue", "view", str(number), "--json", "title,labels"))
        return {**data, "labels": [label["name"] for label in data["labels"]]}


def fill(template: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", value)
    return template


def sources(claims: list[dict]) -> str:
    """The README's Sources section: each verified claim, its quoted line, and its text-fragment link."""
    lines = [f'- {c["claim"]} "{evidence.normalise(c["quote"])}" ([source]({c["link"]}))' for c in claims]
    return f"{SOURCES}\n\n{SOURCES_INTRO}\n\n" + "\n".join(lines) + "\n"


def verified_claims(path: Path) -> list[dict]:
    """The claims of a citations file, refused unless every one is checked and found."""
    try:
        claims = json.loads(path.read_text())
    except FileNotFoundError:
        raise Refused(f"{path}: no citations.json; research-video writes it") from None
    except json.JSONDecodeError as error:
        raise Refused(f"{path}: citations.json is not valid JSON ({error})") from None
    if problems := evidence.gate_problems(claims):
        raise Refused(f"{path}: citations not verified:\n  " + "\n  ".join(problems))
    return claims


def with_video(readme: str, url: str, claims: list[dict]) -> str:
    """The README with its Video line linking url and its Sources section rebuilt from claims."""
    lines = readme.split("\n")
    video = [i for i, line in enumerate(lines) if line.startswith(VIDEO_LINE)]
    starts = [i for i, line in enumerate(lines) if line == SOURCES]
    if len(video) != 1 or len(starts) != 1:
        raise Refused(f"the README needs exactly one '{VIDEO_LINE}' line and one '{SOURCES}' heading")
    lines[video[0]] = VIDEO_LINE + url
    start = starts[0]
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    tail = "\n" + "\n".join(lines[end:]) if end < len(lines) else ""
    return "\n".join(lines[:start]) + "\n" + sources(claims) + tail


def scaffold(channel: str, number: int, slug: str, proves: str, root: Path, gh) -> tuple[Path, str]:
    """Create the demo folder; return it and its description link."""
    config = youtube_channel.load(channel, root).config
    if not youtube_channel.NAME.fullmatch(slug):
        raise BadInput(f"slug {slug!r} must be lowercase words joined by hyphens, such as mocked-tests")
    repo, clone = config["demos"]["repo"], root / ".projects" / "content" / config["demos"]["path"]
    folder = clone / f"{number}-{slug}"
    if not clone.is_dir():
        raise Refused(f"the clone of {repo} is missing at {clone.relative_to(root)}; the owner clones it there")
    if not (clone / ".git").exists():
        raise Refused(f"{clone.relative_to(root)} is not a git repository; the owner clones {repo} there")
    if folder.exists():
        raise Refused(f"{folder.relative_to(root)} already exists; continue it or pick another slug")
    if not gh.repo_exists(repo):
        raise Refused(f"{repo} does not exist on GitHub; the owner creates it once (public, MIT) and clones it")
    claims = verified_claims(youtube_channel.workspace(channel, root) / "videos" / str(number) / "citations.json")
    issue = gh.issue_link(number)
    if config["labels"]["channel"] not in issue["labels"]:
        raise BadInput(f"#{number} is not a content issue of {channel} (no {config['labels']['channel']} label)")
    link = f"https://github.com/{repo}/tree/main/{folder.name}"
    values = {
        "title": issue["title"],
        "channel": config["name"],
        "channel_url": config["url"],
        "proves": proves.strip(),
        "video": VIDEO_PENDING,
        "sources": sources(claims).rstrip("\n"),
        "link": link,
        "folder": folder.name,
        "prompt": channel,
    }
    references = SKILL / "references"
    readme = fill((references / "readme-template.md").read_text(), values)
    tape = fill((references / "demo.tape").read_text(), values)
    for part in ("demo", "tests"):
        (folder / part).mkdir(parents=True)
        (folder / part / ".gitkeep").write_text("")
    (folder / "README.md").write_text(readme)
    (folder / "demo.tape").write_text(tape)
    (folder / ".gitignore").write_text(MEDIA_IGNORE)
    return folder, link


def main(argv: list[str] | None = None, root: Path = REPO_ROOT, gh=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("channel")
    parser.add_argument("number", type=int)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--proves", required=True, help="what the demo proves, in one sentence")
    args = parser.parse_args(argv)
    try:
        folder, link = scaffold(args.channel, args.number, args.slug, args.proves, root, gh or GitHub())
    except (youtube_channel.ChannelError, BadInput) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    except Refused as error:
        print(f"refused: {error}", file=sys.stderr)
        return 3
    except (github_issues.GitHubError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"created: {folder.relative_to(root)}")
    print(link)
    return 0


if __name__ == "__main__":
    sys.exit(main())
