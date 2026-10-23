"""Read and write content issues: the only door to their labels and body.

Usage: uv run agentic/scripts/content_issue.py COMMAND [ARGS]

  new CHANNEL --type long-form|short --title TITLE [--brief-file FILE]
      [--parent N | --related N]
                      file a video at stage idea and create its videos/<issue-number>/ folder;
                      a Short cut from long-form N is its sub-issue (--parent), and an
                      independent Short is standalone, linking long-form N (--related)
  stage N STAGE       move a video to its next stage, with a YouTube: comment
  status [N] [--channel CHANNEL]
                      JSON for one video (stage, next stage, open gate, links, folder), or
                      the queue of open videos, those waiting for the owner first
  gate N GATE --request | --approve
                      mark the video waiting for the owner at a gate, or record the
                      owner's yes as a "YouTube: gate N approved." comment

A content issue is one video (D-042): labels kind:youtube, channel:<name>,
content-type:*, and one youtube-stage:*, a body with a Brief section, and
YouTube: comments for each state change. Labels, stages, and gates are in
config/content.yaml. A video moves only to the next stage, and leaves a gate's
stage only after that gate's approval: gate 1 the idea and angle, gate 2 the
researched script and demo plan, gate 3 the final video.

Exit codes: 0 done, 1 GitHub, config, or file error, 2 bad input or an invalid
channel, 3 refused (a move the stages or gates do not allow, or a Short's link
to anything but a long-form video of its channel).
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml
import youtube_channel
from github_issues import GitHub, GitHubError

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG = REPO_ROOT / "config" / "content.yaml"
FACTORY_CONFIG = REPO_ROOT / "config" / "factory.yaml"

KIND = "kind:youtube"
OWNER = "needs:owner"
TYPES = ["long-form", "short"]

APPROVED = re.compile(r"YouTube: gate (\d+) approved\.")
PARENT = re.compile(r"^Cut from long-form #(\d+)\.$", re.MULTILINE)
RELATED = re.compile(r"^Related long-form: #(\d+)\.$", re.MULTILINE)


class Error(Exception):
    """Config failure: exit 1, like a GitHubError."""


class BadInput(Exception):
    """Input this script cannot accept: exit 2."""


class Refused(Exception):
    """A move the stages or gates do not allow, or a Short's link to anything but a long-form: exit 3."""


@dataclass
class Config:
    labels: dict[str, tuple[str, str]]
    stages: list[str]
    gates: dict[int, str]  # gate -> the stage it closes
    channel_label: tuple[str, str]


def _pair(value, what: str, path: Path) -> tuple[str, str]:
    if not (isinstance(value, list) and len(value) == 2 and all(isinstance(v, str) for v in value)):
        raise Error(f"{path.name}: {what} needs [color, description]")
    return value[0].lower(), value[1]


def load_config(path: Path, factory: Path) -> Config:
    """Parse config/content.yaml, plus needs:owner from config/factory.yaml. Raises Error when invalid."""
    data = yaml.safe_load(path.read_text()) or {}
    labels, gates = data.get("labels"), data.get("gates")
    if not isinstance(labels, dict) or not isinstance(gates, dict):
        raise Error(f"{path.name}: needs 'labels' and 'gates' mappings")
    parsed = {str(name): _pair(value, f"label {name!r}", path) for name, value in labels.items()}
    stages = [name.split(":", 1)[1] for name in parsed if name.startswith("youtube-stage:")]
    for name in (KIND, *(f"content-type:{t}" for t in TYPES)):
        if name not in parsed:
            raise Error(f"{path.name}: missing label {name!r}")
    if not stages or any(stage not in stages[:-1] for stage in gates.values()):
        raise Error(f"{path.name}: each gate must close a youtube-stage that is not the last")
    owner = (yaml.safe_load(factory.read_text()) or {}).get("labels", {}).get(OWNER)
    parsed[OWNER] = _pair(owner, f"label {OWNER!r}", factory)
    return Config(
        parsed, stages, {int(k): v for k, v in gates.items()}, _pair(data.get("channel_label"), "channel_label", path)
    )


# Body


def quote(text: str) -> str:
    """The brief as a block quote, so its headings stay inert."""
    lines = text.strip().replace("\r\n", "\n").split("\n")
    return "\n".join(f"> {line}" if line.strip() else ">" for line in lines) if text.strip() else "> (empty)"


def render_body(sections: dict[str, str]) -> str:
    return "\n".join(f"## {name}\n\n{text}\n" for name, text in sections.items())


# Labels, stages, and gates


def family(labels: list[str], prefix: str) -> list[str]:
    return [label.split(":", 1)[1] for label in labels if label.startswith(f"{prefix}:")]


def require_video(issue: dict) -> tuple[str, str, str]:
    """(stage, type, channel label value) of a content issue with clean labels. Raises Refused otherwise."""
    if KIND not in issue["labels"]:
        raise Refused(f"#{issue['number']} is not a content issue; file it with 'new'")
    found = {name: family(issue["labels"], name) for name in ("youtube-stage", "content-type", "channel")}
    for name, values in found.items():
        if len(values) != 1:
            raise Refused(f"#{issue['number']} needs exactly one {name} label, not {len(values)}")
    return found["youtube-stage"][0], found["content-type"][0], found["channel"][0]


def approved_gates(comments: list[str]) -> list[int]:
    """Gates the owner approved, from the script's `YouTube: gate N approved.` comments."""
    return sorted({int(m[1]) for c in comments if (m := APPROVED.match(c.strip()))})


def check_move(current: str, target: str, approved: list[int], config: Config) -> None:
    """Allow only the next stage, and never out of a gate's stage without its approval."""
    if target not in config.stages:
        raise BadInput(f"unknown stage {target!r}; the stages are {', '.join(config.stages)}")
    if current not in config.stages:
        raise Refused(f"unknown current stage {current!r}; fix the youtube-stage label")
    index = config.stages.index(current)
    following = config.stages[index + 1] if index + 1 < len(config.stages) else None
    if target != following:
        allowed = f"only to {following}" if following else "no further"
        raise Refused(f"a video moves one stage forward; from {current} it moves {allowed}, not to {target}")
    for gate, stage in config.gates.items():
        if stage == current and gate not in approved:
            raise Refused(
                f"leaving {current} passes gate {gate}; record the owner's yes with 'gate <n> {gate} --approve'"
            )


# Commands


def read_file(path: str) -> str:
    try:
        return Path(path).read_text()
    except OSError as error:
        raise BadInput(f"cannot read {path}: {error.strerror}") from error


def ensure_labels(gh: GitHub, wanted: dict[str, tuple[str, str]]) -> None:
    """Create or update each wanted label that GitHub lacks or holds differently."""
    existing = gh.labels()
    for name, value in wanted.items():
        if existing.get(name) != value:
            gh.save_label(name, *value, exists=name in existing)


def check_long_form(gh: GitHub, number: int, label: str) -> None:
    """Refuse a link to anything but a long-form video of the same channel."""
    _, kind, channel = require_video(gh.issue(number))
    if kind != "long-form" or f"channel:{channel}" != label:
        raise Refused(f"#{number} is not a long-form video of {label}; a Short links only to one")


def cmd_new(gh: GitHub, config: Config, args: argparse.Namespace, root: Path) -> int:
    channel = youtube_channel.load(args.channel, root)
    if not args.title.strip():
        raise BadInput("the title is empty")
    long_form = args.parent or args.related
    if long_form and args.type != "short":
        raise BadInput("only a Short links to a long-form video")
    brief = read_file(args.brief_file) if args.brief_file else ""
    label = channel.config["labels"]["channel"]
    if long_form:
        check_long_form(gh, long_form, label)
    link = f"Cut from long-form #{args.parent}." if args.parent else f"Related long-form: #{args.related}."
    text = f"{link}\n\n{quote(brief)}" if long_form else quote(brief)
    color, description = config.channel_label
    ensure_labels(gh, {**config.labels, label: (color, description.format(name=channel.config["name"]))})
    labels = [KIND, label, f"content-type:{args.type}", f"youtube-stage:{config.stages[0]}"]
    number = gh.create(args.title.strip(), render_body({"Brief": text}), labels)
    try:
        (channel.workspace / "videos" / str(number)).mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise Error(f"#{number} filed, but its folder videos/{number}/ failed: {error.strerror}") from error
    if args.parent:
        try:
            gh.add_sub_issue(args.parent, number)
        except GitHubError as error:
            raise GitHubError(f"#{number} filed, but linking it under #{args.parent} failed: {error}") from error
    gh.comment(number, f"YouTube: filed for channel `{args.channel}`; stage `{config.stages[0]}`.")
    print(f"#{number}: {args.type} video at stage {config.stages[0]}")
    return 0


def video_status(issue: dict, config: Config) -> dict:
    stage, kind, channel = require_video(issue)
    if stage not in config.stages:
        raise Refused(f"unknown stage {stage!r} on #{issue['number']}; fix the youtube-stage label")
    approved = approved_gates(issue["comments"])
    index = config.stages.index(stage)
    gate = next((g for g, s in config.gates.items() if s == stage and g not in approved), None)
    parent = PARENT.search(issue["body"])
    link = parent or RELATED.search(issue["body"])
    return {
        "number": issue["number"],
        "title": issue["title"],
        "state": issue["state"],
        "channel": channel,
        "type": kind,
        "stage": stage,
        "next": config.stages[index + 1] if index + 1 < len(config.stages) else None,
        "gate": gate,
        "approved": approved,
        "waiting": OWNER in issue["labels"],
        "long_form": int(link[1]) if link else None,
        "parent": int(parent[1]) if parent else None,
        "folder": f"videos/{issue['number']}",
    }


def queue(issues: list[dict], config: Config, label: str | None) -> list[dict]:
    """Open videos, of one channel label when given: those waiting for the owner first, then the furthest along."""
    rows = []
    for issue in issues:
        if KIND not in issue["labels"] or (label and label not in issue["labels"]):
            continue
        stages, kinds = family(issue["labels"], "youtube-stage"), family(issue["labels"], "content-type")
        rows.append(
            {
                "number": issue["number"],
                "title": issue["title"],
                "type": kinds[0] if len(kinds) == 1 else None,
                "stage": stages[0] if len(stages) == 1 else None,
                "waiting": OWNER in issue["labels"],
            }
        )
    rank = {stage: index for index, stage in enumerate(config.stages)}
    return sorted(rows, key=lambda row: (not row["waiting"], -rank.get(row["stage"], -1), row["number"]))


def cmd_status(gh: GitHub, config: Config, args: argparse.Namespace, root: Path) -> int:
    label = youtube_channel.load(args.channel, root).config["labels"]["channel"] if args.channel else None
    if args.number is None:
        print(json.dumps(queue(gh.open_issues(), config, label), indent=2))
        return 0
    row = video_status(gh.issue(args.number), config)
    if label and f"channel:{row['channel']}" != label:
        raise Refused(f"#{args.number} is a video of channel:{row['channel']}, not {label}")
    print(json.dumps(row, indent=2))
    return 0


def cmd_stage(gh: GitHub, config: Config, args: argparse.Namespace, root: Path) -> int:
    issue = gh.issue(args.number)
    current, _, _ = require_video(issue)
    check_move(current, args.stage, approved_gates(issue["comments"]), config)
    # A video moves only once the owner has answered, so a move also ends any wait for the owner.
    remove = [f"youtube-stage:{current}"] + ([OWNER] if OWNER in issue["labels"] else [])
    gh.edit(args.number, add=[f"youtube-stage:{args.stage}"], remove=remove)
    gh.comment(args.number, f"YouTube: stage `{current}` -> `{args.stage}`.")
    print(f"#{args.number}: {current} -> {args.stage}")
    return 0


def cmd_gate(gh: GitHub, config: Config, args: argparse.Namespace, root: Path) -> int:
    issue = gh.issue(args.number)
    current, _, _ = require_video(issue)
    if args.gate not in config.gates:
        raise BadInput(f"unknown gate {args.gate}; the gates are {', '.join(map(str, config.gates))}")
    stage = config.gates[args.gate]
    if current != stage:
        raise Refused(f"gate {args.gate} is decided at stage {stage}; #{args.number} is at {current}")
    if args.gate in approved_gates(issue["comments"]):
        print(f"#{args.number}: gate {args.gate} already approved")
        return 0
    if args.request:
        if OWNER not in issue["labels"]:
            gh.edit(args.number, add=[OWNER])
        gh.comment(args.number, f"YouTube: gate {args.gate} needs the owner.")
        print(f"#{args.number}: gate {args.gate} waits for the owner")
        return 0
    # Gate checks that can refuse an approval, such as gate 2's citations (AC17), go here.
    gh.comment(args.number, f"YouTube: gate {args.gate} approved.")
    if OWNER in issue["labels"]:
        gh.edit(args.number, remove=[OWNER])
    print(f"#{args.number}: gate {args.gate} approved")
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = root.add_subparsers(dest="command", required=True)

    p = commands.add_parser("new", help="file a video at stage idea")
    p.add_argument("channel")
    p.add_argument("--type", required=True, choices=TYPES)
    p.add_argument("--title", required=True)
    p.add_argument("--brief-file", help="file holding the idea's brief")
    group = p.add_mutually_exclusive_group()
    group.add_argument("--parent", type=int, help="the long-form a Short is cut from; links it as a sub-issue")
    group.add_argument("--related", type=int, help="the long-form an independent Short links to")

    p = commands.add_parser("stage", help="move a video to its next stage")
    p.add_argument("number", type=int)
    p.add_argument("stage")

    p = commands.add_parser("gate", help="ask the owner at a gate, or record the owner's yes")
    p.add_argument("number", type=int)
    p.add_argument("gate", type=int)
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--request", action="store_true", help="mark the video waiting for the owner at this gate")
    group.add_argument("--approve", action="store_true", help="only after the owner's explicit yes")

    p = commands.add_parser("status", help="JSON for one video, or the queue of open videos")
    p.add_argument("number", type=int, nargs="?")
    p.add_argument("--channel", help="only this channel's videos; with N, refuse a video of another channel")
    return root


COMMANDS = {"new": cmd_new, "stage": cmd_stage, "gate": cmd_gate, "status": cmd_status}


def main(
    argv: list[str] | None = None,
    gh: GitHub | None = None,
    root: Path = REPO_ROOT,
    config: Path = CONFIG,
    factory: Path = FACTORY_CONFIG,
) -> int:
    args = parser().parse_args(argv)
    try:
        return COMMANDS[args.command](gh or GitHub(), load_config(config, factory), args, root)
    except (BadInput, youtube_channel.ChannelError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    except Refused as error:
        print(f"refused: {error}", file=sys.stderr)
        return 3
    except (Error, GitHubError, OSError, yaml.YAMLError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
