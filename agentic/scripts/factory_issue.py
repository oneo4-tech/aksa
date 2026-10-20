"""Read and write factory issues: the only door to their labels and body.

Usage: uv run agentic/scripts/factory_issue.py COMMAND [ARGS]

  intake --title TITLE --request-file FILE   file a new factory issue from a plain-text request
  intake --issue N                           adopt an existing issue; its body becomes the Request
  section N {Concept,Requirement,Spec} --file FILE
                                             write one prose section of the body
  set N [--type T] [--size S] [--title T] [--pr P] [--owner wait|clear]
  stage N STAGE [--reason TEXT]              move to another stage, with a Factory: comment
  task N --plan FILE | --done Tk             write the task checklist, or tick a landed task
  claim N --session ID [--takeover]          hold the issue for this session
  release N --session ID [--takeover]        end the claim
  status [N]                                 JSON for one issue, or the queue of open factory issues
  labels [--check]                           create or update the labels in config/factory.yaml

A factory issue's state is its labels, its body sections, and its Factory: comments
(agentic/rules/factory.md). Every write is checked first: one label per family, only
the stage moves the lifecycle allows, prose sections without second-level headings
or checkboxes, and a Delivery section this script can read back. A --plan file has
one task per line as "<slug>: <title>".

Exit codes: 0 done, 1 GitHub or config error, 2 bad input, 3 refused (a held claim
or a move the lifecycle does not allow).
"""

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG = REPO_ROOT / "config" / "factory.yaml"

STAGES = ["triage", "concept", "define", "spec", "plan", "build", "ship"]
SECTIONS = ["Request", "Concept", "Requirement", "Spec", "Delivery"]
PROSE = ["Concept", "Requirement", "Spec"]

TITLE = re.compile(r"(?P<prefix>[a-z]+)(\([a-z0-9-]+\))?!?: (?P<summary>\S.*)")
TASK = re.compile(r"- \[(?P<done>[ xX])\] T(?P<id>\d+): (?P<title>.+) \(branch `(?P<branch>[^`]+)`\)")
SLUG = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")
SESSION = re.compile(r"[A-Za-z0-9._-]+")
CLAIM = re.compile(r"Factory: claimed by session `(?P<session>[^`]+)`(?P<takeover>, taking over)?")
RELEASE = re.compile(r"Factory: released by session `(?P<session>[^`]+)`(, for `(?P<holder>[^`]+)`)?")


class Error(Exception):
    """GitHub or config failure: exit 1."""


class BadInput(Exception):
    """Input this script cannot accept: exit 2."""


class Refused(Exception):
    """A held claim or a move the lifecycle does not allow: exit 3."""


@dataclass
class Config:
    prefixes: dict[str, str]
    labels: dict[str, tuple[str, str]]

    def family(self, name: str) -> list[str]:
        """Values of a label family in config order, such as the stages for "stage"."""
        return [label.split(":", 1)[1] for label in self.labels if label.startswith(f"{name}:")]


def load_config(path: Path) -> Config:
    """Parse config/factory.yaml. Raises Error when it does not match the lifecycle."""
    data = yaml.safe_load(path.read_text()) or {}
    prefixes, labels = data.get("prefixes"), data.get("labels")
    if not isinstance(prefixes, dict) or not isinstance(labels, dict):
        raise Error(f"{path.name}: needs 'prefixes' and 'labels' mappings")
    parsed: dict[str, tuple[str, str]] = {}
    for name, value in labels.items():
        if not (isinstance(value, list) and len(value) == 2 and all(isinstance(v, str) for v in value)):
            raise Error(f"{path.name}: label {name!r} needs [color, description]")
        parsed[str(name)] = (value[0].lower(), value[1])
    config = Config({str(k): str(v) for k, v in prefixes.items()}, parsed)
    if config.family("stage") != STAGES:
        raise Error(f"{path.name}: stage labels must be, in order: {', '.join(STAGES)}")
    if set(config.family("type")) != set(config.prefixes):
        raise Error(f"{path.name}: type labels and prefixes must name the same types")
    for name in ("needs:owner", "claimed"):
        if name not in parsed:
            raise Error(f"{path.name}: missing label {name!r}")
    return config


# Body sections


def parse_body(text: str) -> dict[str, str]:
    """Section name -> content. Raises BadInput when the body is not a factory issue body."""
    sections: dict[str, list[str]] = {}
    current = None
    for line in text.replace("\r\n", "\n").split("\n"):
        if line.startswith("## "):
            name = line[3:].strip()
            if name not in SECTIONS or name in sections:
                raise BadInput(f"unexpected heading {line!r}; a factory issue has only {', '.join(SECTIONS)}")
            current = name
            sections[name] = []
        elif current is not None:
            sections[current].append(line)
        elif line.strip():
            raise BadInput("text before the first section; adopt the issue with 'intake --issue'")
    return {name: "\n".join(lines).strip() for name, lines in sections.items()}


def render_body(sections: dict[str, str]) -> str:
    return "\n".join(f"## {name}\n\n{sections[name]}\n" for name in SECTIONS if name in sections)


def quote(text: str) -> str:
    """The request as a block quote, so its headings stay inert; its checkboxes are escaped so they are not tasks."""
    lines = [
        re.sub(r"^(\s*[-*] )\[([ xX])\]", r"\1\\[\2]", line) for line in text.strip().replace("\r\n", "\n").split("\n")
    ]
    return "\n".join(f"> {line}" if line.strip() else ">" for line in lines) if text.strip() else "> (empty)"


def check_prose(name: str, text: str) -> str:
    text = text.strip()
    if not text:
        raise BadInput(f"{name}: the section is empty")
    for line in text.split("\n"):
        if line.startswith("## "):
            raise BadInput(f"{name}: use '###' headings; '## ' starts a new section")
        if re.match(r"\s*[-*] \[[ xX]\]", line):
            raise BadInput(f"{name}: checkboxes belong only to the Delivery task checklist")
    return text


# Delivery section


@dataclass
class Task:
    id: int
    title: str
    branch: str
    done: bool = False

    def line(self) -> str:
        return f"- [{'x' if self.done else ' '}] T{self.id}: {self.title} (branch `{self.branch}`)"


@dataclass
class Delivery:
    branch: str | None = None
    pr: int | None = None
    tasks: list[Task] = field(default_factory=list)


def parse_delivery(text: str) -> Delivery:
    delivery = Delivery()
    for line in (line.strip() for line in text.split("\n")):
        if not line or line in ("Branch: none", "PR: none"):
            continue
        if match := re.fullmatch(r"Branch: `([^`]+)`", line):
            delivery.branch = match[1]
        elif match := re.fullmatch(r"PR: #(\d+)", line):
            delivery.pr = int(match[1])
        elif match := TASK.fullmatch(line):
            delivery.tasks.append(Task(int(match["id"]), match["title"], match["branch"], match["done"] != " "))
        else:
            raise BadInput(f"Delivery: unreadable line {line!r}")
    return delivery


def render_delivery(delivery: Delivery) -> str:
    lines = [
        f"Branch: `{delivery.branch}`" if delivery.branch else "Branch: none",
        f"PR: #{delivery.pr}" if delivery.pr else "PR: none",
    ]
    if delivery.tasks:
        lines += ["", *(task.line() for task in delivery.tasks)]
    return "\n".join(lines)


# Labels, stages, titles, branches, and claims


def label_values(labels: list[str], config: Config) -> dict[str, list[str]]:
    """Factory label values on an issue, by family."""
    return {
        family: [
            label.split(":", 1)[1] for label in labels if label in config.labels and label.startswith(f"{family}:")
        ]
        for family in ("stage", "type", "size")
    }


def require_factory(issue: dict, config: Config) -> tuple[str, str | None, str | None]:
    """(stage, type, size) of a factory issue whose labels are clean. Raises Refused otherwise."""
    values = label_values(issue["labels"], config)
    if not values["stage"]:
        raise Refused(f"#{issue['number']} is not a factory issue; file it with 'intake'")
    for family, found in values.items():
        if len(found) > 1:
            raise Refused(f"#{issue['number']} has more than one {family} label: {', '.join(found)}")
    return values["stage"][0], next(iter(values["type"]), None), next(iter(values["size"]), None)


def check_move(current: str, target: str, size: str | None, reason: str | None) -> None:
    """Allow the forward moves of the lifecycle, and any move back with a reason."""
    if target == current:
        raise Refused(f"the run is already in stage {current}")
    if STAGES.index(target) < STAGES.index(current):
        if not reason:
            raise BadInput(f"moving back from {current} to {target} needs --reason")
        return
    if current == "define" and size is None:
        raise Refused("set the size at G1 before leaving define")
    forward = {
        "triage": ["concept", "define"],
        "concept": ["define"],
        "define": ["spec" if size == "large" else "build"],
        "spec": ["plan"],
        "plan": ["build"],
        "build": ["ship"],
    }
    if target not in forward.get(current, []):
        raise Refused(f"{current} cannot move to {target}; see the lifecycle in agentic/rules/factory.md")


def check_title(title: str, run_type: str, config: Config) -> None:
    match = TITLE.fullmatch(title)
    prefix = config.prefixes[run_type]
    if not match or match["prefix"] != prefix:
        raise BadInput(f"a {run_type} run's title is '{prefix}(<scope>): <summary>', not {title!r}")


def slugify(text: str, words: int = 5) -> str:
    return "-".join(re.findall(r"[a-z0-9]+", text.lower())[:words])


def delivery_branch(number: int, title: str, size: str, prefix: str) -> str:
    match = TITLE.fullmatch(title)
    if not match:
        raise Refused(f"title {title!r} is not '<prefix>(<scope>): <summary>'; set it at G1 with 'set --title'")
    slug = slugify(match["summary"])
    return f"int/{number}-{slug}" if size == "large" else f"{prefix}/{number}-{slug}"


def claim_holder(comments: list[str]) -> str | None:
    """The session holding the claim. The first claim while free wins; a takeover replaces the holder."""
    holder = None
    for comment in comments:
        first = comment.strip().split("\n", 1)[0]
        claim, release = CLAIM.match(first), RELEASE.match(first)
        if claim and (holder is None or claim["takeover"]):
            holder = claim["session"]
        elif release and holder in (release["session"], release["holder"]):
            holder = None
    return holder


def issue_status(issue: dict, config: Config) -> dict:
    labels, problems = issue["labels"], []
    values = label_values(labels, config)
    for family, found in values.items():
        if len(found) > 1:
            problems.append(f"more than one {family} label: {', '.join(found)}")
    if not values["stage"]:
        problems.append("no stage label")
    stage = values["stage"][0] if len(values["stage"]) == 1 else None
    run_type = values["type"][0] if len(values["type"]) == 1 else None
    size = values["size"][0] if len(values["size"]) == 1 else None
    after_define = stage in STAGES[STAGES.index("define") + 1 :]
    if after_define and run_type is None:
        problems.append("no type label after define")
    if after_define and size is None:
        problems.append("no size label after define")
    if after_define and run_type and not re.match(rf"{config.prefixes[run_type]}[(:!]", issue["title"]):
        problems.append(f"title does not start with the {run_type} prefix")
    try:
        sections = parse_body(issue["body"])
        delivery = parse_delivery(sections.get("Delivery", ""))
        if "Request" not in sections:
            problems.append("no Request section")
    except BadInput as error:
        problems.append(f"body: {error}")
        delivery = Delivery()
    if stage in ("build", "ship") and not delivery.branch:
        problems.append("no delivery branch")
    if stage in ("build", "ship") and size == "large" and not delivery.tasks:
        problems.append("a large run without tasks")
    done = [task.done for task in delivery.tasks]
    if done != sorted(done, reverse=True):
        problems.append("tasks landed out of order")
    holder = claim_holder(issue["comments"])
    if ("claimed" in labels) != (holder is not None):
        problems.append("the claimed label and the claim comments disagree")
    return {
        "number": issue["number"],
        "title": issue["title"],
        "state": issue["state"],
        "stage": stage,
        "type": run_type,
        "size": size,
        "needs_owner": "needs:owner" in labels,
        "claim": holder,
        "branch": delivery.branch,
        "pr": delivery.pr,
        "tasks": [{"id": f"T{t.id}", "title": t.title, "branch": t.branch, "done": t.done} for t in delivery.tasks],
        "next_task": next((f"T{t.id}" for t in delivery.tasks if not t.done), None),
        "problems": problems,
    }


def queue(issues: list[dict], config: Config) -> list[dict]:
    """Open factory issues: those waiting for the owner first, then the furthest along."""
    rows = []
    for issue in issues:
        stages = label_values(issue["labels"], config)["stage"]
        if stages:
            stage = stages[0] if len(stages) == 1 else None
            rows.append(
                {
                    "number": issue["number"],
                    "title": issue["title"],
                    "stage": stage,
                    "needs_owner": "needs:owner" in issue["labels"],
                    "claimed": "claimed" in issue["labels"],
                }
            )
    rank = {stage: index for index, stage in enumerate(STAGES)}
    return sorted(rows, key=lambda row: (not row["needs_owner"], -rank.get(row["stage"], -1), row["number"]))


def label_plan(existing: dict[str, tuple[str, str]], config: Config) -> list[tuple[str, str]]:
    """(action, label) for each config label missing from, or different on, GitHub. Never deletes."""
    return [
        ("create" if name not in existing else "update", name)
        for name, wanted in config.labels.items()
        if existing.get(name) != wanted
    ]


# GitHub


class GitHub:
    """The thin layer over the gh CLI; tests replace it with a fake."""

    def _gh(self, *args: str, stdin: str | None = None) -> str:
        result = subprocess.run(["gh", *args], input=stdin, capture_output=True, text=True, check=False)
        if result.returncode:
            raise Error(f"gh {' '.join(args[:2])} failed: {result.stderr.strip()}")
        return result.stdout

    def issue(self, number: int) -> dict:
        fields = "number,title,state,body,labels,comments"
        data = json.loads(self._gh("issue", "view", str(number), "--json", fields))
        data["labels"] = [label["name"] for label in data["labels"]]
        data["comments"] = [comment["body"] for comment in data["comments"]]
        return data

    def open_issues(self) -> list[dict]:
        data = json.loads(
            self._gh("issue", "list", "--state", "open", "--limit", "500", "--json", "number,title,labels")
        )
        return [{**issue, "labels": [label["name"] for label in issue["labels"]]} for issue in data]

    def create(self, title: str, body: str, labels: list[str]) -> int:
        flags = [flag for label in labels for flag in ("--label", label)]
        url = self._gh("issue", "create", "--title", title, "--body-file", "-", *flags, stdin=body).strip()
        return int(url.rsplit("/", 1)[1])

    def edit(
        self,
        number: int,
        body: str | None = None,
        title: str | None = None,
        add: list[str] | None = None,
        remove: list[str] | None = None,
    ) -> None:
        args = ["issue", "edit", str(number)]
        args += ["--body-file", "-"] if body is not None else []
        args += ["--title", title] if title is not None else []
        args += [flag for label in add or [] for flag in ("--add-label", label)]
        args += [flag for label in remove or [] for flag in ("--remove-label", label)]
        self._gh(*args, stdin=body)

    def comment(self, number: int, text: str) -> None:
        self._gh("issue", "comment", str(number), "--body-file", "-", stdin=text)

    def labels(self) -> dict[str, tuple[str, str]]:
        data = json.loads(self._gh("label", "list", "--limit", "500", "--json", "name,color,description"))
        return {label["name"]: (label["color"].lower(), label["description"] or "") for label in data}

    def save_label(self, name: str, color: str, description: str, exists: bool) -> None:
        self._gh("label", "edit" if exists else "create", name, "--color", color, "--description", description)


# Commands


def read_file(path: str) -> str:
    try:
        return Path(path).read_text()
    except OSError as error:
        raise BadInput(f"cannot read {path}: {error.strerror}") from error


def cmd_intake(gh: GitHub, config: Config, args: argparse.Namespace) -> int:
    if args.issue is not None:
        issue = gh.issue(args.issue)
        if label_values(issue["labels"], config)["stage"]:
            raise Refused(f"#{args.issue} is already a factory issue")
        gh.edit(args.issue, body=render_body({"Request": quote(issue["body"])}), add=["stage:triage"])
        gh.comment(args.issue, "Factory: adopted as a factory issue; stage `triage`.")
        print(f"adopted #{args.issue}")
        return 0
    if not (args.title and args.request_file):
        raise BadInput("intake needs --issue, or --title with --request-file")
    number = gh.create(args.title, render_body({"Request": quote(read_file(args.request_file))}), ["stage:triage"])
    gh.comment(number, "Factory: filed from a work request; stage `triage`.")
    print(f"created #{number}")
    return 0


def cmd_section(gh: GitHub, config: Config, args: argparse.Namespace) -> int:
    text = check_prose(args.name, read_file(args.file))
    issue = gh.issue(args.number)
    require_factory(issue, config)
    sections = parse_body(issue["body"])
    sections[args.name] = text
    gh.edit(args.number, body=render_body(sections))
    print(f"wrote {args.name} on #{args.number}")
    return 0


def cmd_set(gh: GitHub, config: Config, args: argparse.Namespace) -> int:
    if not any((args.type, args.size, args.title, args.pr, args.owner)):
        raise BadInput("set needs at least one of --type, --size, --title, --pr, --owner")
    issue = gh.issue(args.number)
    _, run_type, _ = require_factory(issue, config)
    labels, add, remove, changes = issue["labels"], [], [], []
    for family, value in (("type", args.type), ("size", args.size)):
        if value:
            if value not in config.family(family):
                raise BadInput(f"unknown {family} {value!r}; one of {', '.join(config.family(family))}")
            add.append(f"{family}:{value}")
            remove += [label for label in labels if label.startswith(f"{family}:") and label != f"{family}:{value}"]
            changes.append(f"{family} {value}")
    if args.owner == "wait" and "needs:owner" not in labels:
        add.append("needs:owner")
        changes.append("waiting for the owner")
    if args.owner == "clear" and "needs:owner" in labels:
        remove.append("needs:owner")
        changes.append("no longer waiting for the owner")
    if args.title:
        run_type = args.type or run_type
        if run_type is None:
            raise BadInput("set the type before or with the title")
        check_title(args.title, run_type, config)
        changes.append(f"title {args.title!r}")
    body = None
    if args.pr:
        sections = parse_body(issue["body"])
        delivery = parse_delivery(sections.get("Delivery", ""))
        delivery.pr = args.pr
        sections["Delivery"] = render_delivery(delivery)
        body = render_body(sections)
        changes.append(f"pull request #{args.pr}")
    if not changes:
        print(f"#{args.number}: no change")
        return 0
    gh.edit(args.number, body=body, title=args.title, add=add, remove=remove)
    print(f"#{args.number}: {', '.join(changes)}")
    return 0


def cmd_stage(gh: GitHub, config: Config, args: argparse.Namespace) -> int:
    issue = gh.issue(args.number)
    current, run_type, size = require_factory(issue, config)
    check_move(current, args.stage, size, args.reason)
    body = None
    if (args.stage == "build" and size == "small") or args.stage == "plan":
        sections = parse_body(issue["body"])
        delivery = parse_delivery(sections.get("Delivery", ""))
        if not delivery.branch:
            if run_type is None:
                raise Refused("set the type at G1 before naming the delivery branch")
            delivery.branch = delivery_branch(args.number, issue["title"], size or "small", config.prefixes[run_type])
            sections["Delivery"] = render_delivery(delivery)
            body = render_body(sections)
    gh.edit(args.number, body=body, add=[f"stage:{args.stage}"], remove=[f"stage:{current}"])
    note = f" {args.reason}" if args.reason else ""
    gh.comment(args.number, f"Factory: stage `{current}` -> `{args.stage}`.{note}")
    print(f"#{args.number}: {current} -> {args.stage}")
    return 0


def cmd_task(gh: GitHub, config: Config, args: argparse.Namespace) -> int:
    issue = gh.issue(args.number)
    _, run_type, size = require_factory(issue, config)
    sections = parse_body(issue["body"])
    delivery = parse_delivery(sections.get("Delivery", ""))
    if args.plan:
        if size != "large" or run_type is None:
            raise Refused("only a large run with a type has a task checklist")
        landed = [task for task in delivery.tasks if task.done]
        next_id = max((task.id for task in landed), default=0) + 1
        planned = []
        for line in filter(str.strip, read_file(args.plan).split("\n")):
            slug, _, title = (part.strip() for part in line.partition(":"))
            if not SLUG.fullmatch(slug) or not title:
                raise BadInput(f"task line {line!r} is not '<slug>: <title>'")
            branch = f"{config.prefixes[run_type]}/{args.number}-t{next_id}-{slug}"
            planned.append(Task(next_id, title, branch))
            next_id += 1
        if not planned:
            raise BadInput("the plan file has no tasks")
        delivery.tasks = landed + planned
        message = f"#{args.number}: planned {', '.join(f'T{task.id}' for task in planned)}"
    else:
        task = next((t for t in delivery.tasks if f"T{t.id}" == args.done), None)
        if task is None:
            raise BadInput(f"#{args.number} has no task {args.done}")
        if task.done:
            print(f"#{args.number}: {args.done} already landed")
            return 0
        if any(not t.done for t in delivery.tasks[: delivery.tasks.index(task)]):
            raise Refused(f"tasks land in checklist order; an earlier task than {args.done} is open")
        task.done = True
        message = f"#{args.number}: {args.done} landed"
    sections["Delivery"] = render_delivery(delivery)
    gh.edit(args.number, body=render_body(sections))
    print(message)
    return 0


def check_session(session: str) -> None:
    if not SESSION.fullmatch(session):
        raise BadInput(f"session id {session!r} may use letters, digits, '.', '_', and '-' only")


def cmd_claim(gh: GitHub, config: Config, args: argparse.Namespace) -> int:
    check_session(args.session)
    issue = gh.issue(args.number)
    require_factory(issue, config)
    holder = claim_holder(issue["comments"])
    if holder == args.session:
        print(f"#{args.number} is already claimed by this session")
        return 0
    if holder and not args.takeover:
        raise Refused(
            f"#{args.number} is claimed by session `{holder}`; take over only on the owner's yes (--takeover)"
        )
    text = f"Factory: claimed by session `{args.session}`"
    text += f", taking over from `{holder}` with the owner's approval." if holder else "."
    gh.comment(args.number, text)
    if "claimed" not in issue["labels"]:
        gh.edit(args.number, add=["claimed"])
    winner = claim_holder(gh.issue(args.number)["comments"])
    if winner != args.session:
        raise Refused(f"#{args.number} was claimed first by session `{winner}`")
    print(f"claimed #{args.number}")
    return 0


def cmd_release(gh: GitHub, config: Config, args: argparse.Namespace) -> int:
    check_session(args.session)
    issue = gh.issue(args.number)
    holder = claim_holder(issue["comments"])
    if holder is None:
        if "claimed" in issue["labels"]:
            gh.edit(args.number, remove=["claimed"])
        print(f"#{args.number} is not claimed")
        return 0
    if holder != args.session and not args.takeover:
        raise Refused(f"#{args.number} is claimed by session `{holder}`; release it only on the owner's yes")
    text = f"Factory: released by session `{args.session}`"
    text += f", for `{holder}` with the owner's approval." if holder != args.session else "."
    gh.comment(args.number, text)
    gh.edit(args.number, remove=["claimed"])
    print(f"released #{args.number}")
    return 0


def cmd_status(gh: GitHub, config: Config, args: argparse.Namespace) -> int:
    if args.number is None:
        print(json.dumps(queue(gh.open_issues(), config), indent=2))
    else:
        print(json.dumps(issue_status(gh.issue(args.number), config), indent=2))
    return 0


def cmd_labels(gh: GitHub, config: Config, args: argparse.Namespace) -> int:
    existing = gh.labels()
    plan = label_plan(existing, config)
    for action, name in plan:
        print(f"{action} {name}")
        if not args.check:
            gh.save_label(name, *config.labels[name], exists=name in existing)
    if not plan:
        print("labels match config/factory.yaml")
    return 1 if args.check and plan else 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = root.add_subparsers(dest="command", required=True)

    p = commands.add_parser("intake", help="file or adopt a factory issue")
    p.add_argument("--issue", type=int, help="an existing issue to adopt")
    p.add_argument("--title", help="title of a new issue, in the request's own words")
    p.add_argument("--request-file", help="file holding the plain-text request")

    p = commands.add_parser("section", help="write a prose section of the body")
    p.add_argument("number", type=int)
    p.add_argument("name", choices=PROSE)
    p.add_argument("--file", required=True)

    p = commands.add_parser("set", help="set labels, title, or the pull request")
    p.add_argument("number", type=int)
    p.add_argument("--type")
    p.add_argument("--size")
    p.add_argument("--title")
    p.add_argument("--pr", type=int)
    p.add_argument("--owner", choices=["wait", "clear"])

    p = commands.add_parser("stage", help="move to another stage")
    p.add_argument("number", type=int)
    p.add_argument("stage", choices=STAGES)
    p.add_argument("--reason", help="why; required to move back")

    p = commands.add_parser("task", help="write the task checklist or tick a landed task")
    p.add_argument("number", type=int)
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--plan", help="file with one '<slug>: <title>' line per task")
    group.add_argument("--done", help="the task that landed, such as T2")

    for name, text in (("claim", "hold the issue for this session"), ("release", "end the claim")):
        p = commands.add_parser(name, help=text)
        p.add_argument("number", type=int)
        p.add_argument("--session", required=True, help="this session's id, such as <host>-<YYYYMMDD-HHMMSS>")
        p.add_argument("--takeover", action="store_true", help="only after the owner's explicit yes")

    p = commands.add_parser("status", help="JSON for one issue, or the queue")
    p.add_argument("number", type=int, nargs="?")

    p = commands.add_parser("labels", help="create or update the factory labels")
    p.add_argument("--check", action="store_true", help="only report; exit 1 when GitHub differs")
    return root


COMMANDS = {
    "intake": cmd_intake,
    "section": cmd_section,
    "set": cmd_set,
    "stage": cmd_stage,
    "task": cmd_task,
    "claim": cmd_claim,
    "release": cmd_release,
    "status": cmd_status,
    "labels": cmd_labels,
}


def main(argv: list[str] | None = None, gh: GitHub | None = None, config: Path = CONFIG) -> int:
    args = parser().parse_args(argv)
    try:
        return COMMANDS[args.command](gh or GitHub(), load_config(config), args)
    except BadInput as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    except Refused as error:
        print(f"refused: {error}", file=sys.stderr)
        return 3
    except Error as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
