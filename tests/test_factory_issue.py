"""Tests for agentic/scripts/factory_issue.py, against an in-memory GitHub."""

import copy
import json
import re
from pathlib import Path

import factory_issue as fi
import pytest

ROOT = Path(__file__).resolve().parents[1]

BODY = """## Request

> Add a thing.

## Requirement

### Problem

No thing.

## Delivery

Branch: `int/7-add-the-thing`
PR: none

- [x] T1: First slice (branch `feat/7-t1-first`)
- [ ] T2: Second slice (branch `feat/7-t2-second`)
"""


class FakeGitHub:
    """The GitHub layer of factory_issue.py, kept in memory."""

    def __init__(self):
        self.issues = {}
        self.repo_labels = {}

    def add(self, number, title="feat(factory): add the thing", body=BODY, labels=(), comments=()):
        self.issues[number] = {
            "number": number,
            "title": title,
            "state": "OPEN",
            "body": body,
            "labels": list(labels),
            "comments": list(comments),
        }

    def issue(self, number):
        return copy.deepcopy(self.issues[number])

    def open_issues(self):
        return [{k: i[k] for k in ("number", "title", "labels", "body")} for i in self.issues.values()]

    def create(self, title, body, labels):
        number = max(self.issues, default=0) + 1
        self.add(number, title, body, labels)
        return number

    def edit(self, number, body=None, title=None, add=None, remove=None):
        issue = self.issues[number]
        issue["body"] = issue["body"] if body is None else body
        issue["title"] = issue["title"] if title is None else title
        kept = [label for label in issue["labels"] if label not in (remove or [])]
        issue["labels"] = kept + [label for label in add or [] if label not in kept]

    def comment(self, number, text):
        self.issues[number]["comments"].append(text)

    def labels(self):
        return dict(self.repo_labels)

    def save_label(self, name, color, description, exists):
        self.repo_labels[name] = (color, description)


@pytest.fixture
def gh():
    return FakeGitHub()


def run(gh, *argv):
    return fi.main(list(argv), gh=gh)


def sections(gh, number):
    return fi.parse_body(gh.issues[number]["body"])


# intake


def test_intake_files_a_quoted_request_at_triage_as_a_factory_issue(gh, tmp_path):
    request = tmp_path / "request.md"
    request.write_text("Please add a thing.\n\n## Not a section\n- [ ] not a task\n")
    assert run(gh, "intake", "--title", "Add a thing", "--request-file", str(request)) == 0
    issue = gh.issues[1]
    assert issue["labels"] == ["stage:triage", "kind:factory"]
    assert sections(gh, 1) == {"Request": "> Please add a thing.\n>\n> ## Not a section\n> - \\[ ] not a task"}
    assert issue["comments"] == ["Factory: filed from a work request; stage `triage`."]


def test_intake_adopts_an_issue_as_a_factory_issue_and_keeps_its_text_as_the_request(gh):
    gh.add(3, title="Something is broken", body="It breaks.", labels=["bug"])
    assert run(gh, "intake", "--issue", "3") == 0
    assert sections(gh, 3) == {"Request": "> It breaks."}
    assert gh.issues[3]["labels"] == ["bug", "stage:triage", "kind:factory"]


def test_intake_refuses_an_issue_that_is_already_a_factory_issue(gh):
    gh.add(3, labels=["stage:define"])
    assert run(gh, "intake", "--issue", "3") == 3


def test_intake_refuses_a_content_issue_and_leaves_it_unchanged(gh, capsys):
    gh.add(38, title="Video", body="A video.", labels=["kind:youtube", "youtube-stage:idea"])
    before = copy.deepcopy(gh.issues[38])
    assert run(gh, "intake", "--issue", "38") == 3
    assert gh.issues[38] == before
    error = capsys.readouterr().err
    assert "`kind:youtube`" in error
    assert "run-youtube <channel> #38" in error


# section


def test_section_writes_in_order_and_keeps_the_other_sections(gh, tmp_path):
    gh.add(7, labels=["stage:concept"])
    concept = tmp_path / "concept.md"
    concept.write_text("### Destination\n\nA thing.\n")
    assert run(gh, "section", "7", "Concept", "--file", str(concept)) == 0
    body = sections(gh, 7)
    assert list(body) == ["Request", "Concept", "Requirement", "Delivery"]
    assert body["Concept"] == "### Destination\n\nA thing."
    assert body["Requirement"] == "### Problem\n\nNo thing."


@pytest.mark.parametrize("text", ["## Sneaky\n", "- [ ] a box\n", "   * [x] a box\n", "\n"])
def test_section_rejects_section_headings_checkboxes_and_empty_text(gh, tmp_path, text):
    gh.add(7, labels=["stage:define"])
    file = tmp_path / "s.md"
    file.write_text(text)
    assert run(gh, "section", "7", "Requirement", "--file", str(file)) == 2
    assert gh.issues[7]["body"] == BODY


# set


def test_set_replaces_the_type_and_checks_the_title_prefix(gh):
    gh.add(7, title="Add a thing", labels=["stage:define", "type:fix"])
    assert run(gh, "set", "7", "--type", "feature", "--size", "small", "--title", "feat(factory): add a thing") == 0
    assert gh.issues[7]["labels"] == ["stage:define", "type:feature", "size:small"]
    assert gh.issues[7]["title"] == "feat(factory): add a thing"


@pytest.mark.parametrize("title", ["fix(factory): add a thing", "feat add a thing", "feat(Factory): x"])
def test_set_rejects_a_title_that_does_not_fit_the_type(gh, title):
    gh.add(7, title="Add a thing", labels=["stage:define", "type:feature"])
    assert run(gh, "set", "7", "--title", title) == 2
    assert gh.issues[7]["title"] == "Add a thing"


def test_set_records_the_pull_request_and_waits_for_the_owner_with_a_need(gh):
    gh.add(7, labels=["stage:build", "type:feature", "size:large"])
    assert run(gh, "set", "7", "--pr", "12", "--owner", "wait", "--need", "Approve the merge of PR #12.") == 0
    assert fi.parse_delivery(sections(gh, 7)["Delivery"]).pr == 12
    assert "needs:owner" in gh.issues[7]["labels"]
    assert gh.issues[7]["comments"] == ["Factory: needs the owner: Approve the merge of PR #12."]
    assert run(gh, "set", "7", "--owner", "clear") == 0
    assert "needs:owner" not in gh.issues[7]["labels"]


@pytest.mark.parametrize(
    "args",
    [
        ["--owner", "wait"],
        ["--need", "Approve G1."],
        ["--owner", "wait", "--need", "two\nlines"],
        ["--owner", "wait", "--need", " "],
    ],
)
def test_set_refuses_a_wait_without_one_stated_need(gh, args):
    gh.add(7, labels=["stage:define"])
    assert run(gh, "set", "7", *args) == 2
    assert gh.issues[7]["labels"] == ["stage:define"]
    assert gh.issues[7]["comments"] == []


def test_set_refuses_an_issue_with_two_stage_labels(gh):
    gh.add(7, labels=["stage:define", "stage:build"])
    assert run(gh, "set", "7", "--size", "small") == 3


# stage


def test_stage_moves_forward_with_a_comment(gh):
    gh.add(7, labels=["stage:triage"])
    assert run(gh, "stage", "7", "concept", "--reason", "Open decisions.") == 0
    assert gh.issues[7]["labels"] == ["stage:concept"]
    assert gh.issues[7]["comments"] == ["Factory: stage `triage` -> `concept`. Open decisions."]


@pytest.mark.parametrize(
    ("labels", "target"),
    [
        (["stage:triage"], "build"),
        (["stage:define", "type:feature", "size:small"], "spec"),
        (["stage:define", "type:feature", "size:large"], "build"),
        (["stage:define", "type:feature"], "build"),
        (["stage:plan", "type:feature", "size:large"], "plan"),
    ],
)
def test_stage_refuses_moves_the_lifecycle_does_not_allow(gh, labels, target):
    gh.add(7, labels=labels)
    assert run(gh, "stage", "7", target) == 3
    assert gh.issues[7]["labels"] == labels


def test_stage_moves_back_only_with_a_reason(gh):
    gh.add(7, labels=["stage:build", "type:feature", "size:large"])
    assert run(gh, "stage", "7", "plan") == 2
    assert run(gh, "stage", "7", "plan", "--reason", "T2 is bigger than planned.") == 0
    assert "stage:plan" in gh.issues[7]["labels"]


@pytest.mark.parametrize("target", ["spec", "plan"])
def test_stage_refuses_spec_and_plan_for_a_small_run(gh, target):
    gh.add(7, labels=["stage:build", "type:fix", "size:small"])
    assert run(gh, "stage", "7", target, "--reason", "Work bigger than the task.") == 3
    assert gh.issues[7]["labels"] == ["stage:build", "type:fix", "size:small"]


def test_stage_move_ends_the_wait_for_the_owner(gh):
    gh.add(9, title="fix(scripts): handle empty labels", body="## Request\n\n> x\n", labels=["stage:define"])
    gh.edit(9, add=["type:fix", "size:small", "needs:owner"])
    assert run(gh, "stage", "9", "build", "--reason", "G1 approved by the owner.") == 0
    assert "needs:owner" not in gh.issues[9]["labels"]


def test_entering_build_names_a_small_runs_branch(gh):
    gh.add(9, title="fix(scripts): Handle Empty  labels!", body="## Request\n\n> x\n", labels=["stage:define"])
    gh.edit(9, add=["type:fix", "size:small"])
    assert run(gh, "stage", "9", "build") == 0
    assert fi.parse_delivery(sections(gh, 9)["Delivery"]).branch == "fix/9-handle-empty-labels"


def test_entering_plan_names_the_integration_branch(gh):
    gh.add(5, title="feat(factory): software factory", body="## Request\n\n> x\n", labels=["stage:spec"])
    gh.edit(5, add=["type:feature", "size:large"])
    assert run(gh, "stage", "5", "plan") == 0
    assert fi.parse_delivery(sections(gh, 5)["Delivery"]).branch == "int/5-software-factory"


# task


def test_task_plan_keeps_landed_tasks_and_numbers_the_rest(gh, tmp_path):
    gh.add(7, labels=["stage:plan", "type:feature", "size:large"])
    plan = tmp_path / "plan.txt"
    plan.write_text("second-again: Second slice, smaller\n\nthird: Third slice\n")
    assert run(gh, "task", "7", "--plan", str(plan)) == 0
    tasks = fi.parse_delivery(sections(gh, 7)["Delivery"]).tasks
    assert [(t.id, t.title, t.branch, t.done) for t in tasks] == [
        (1, "First slice", "feat/7-t1-first", True),
        (2, "Second slice, smaller", "feat/7-t2-second-again", False),
        (3, "Third slice", "feat/7-t3-third", False),
    ]


def test_task_plan_rejects_a_line_without_a_slug(gh, tmp_path):
    gh.add(7, labels=["stage:plan", "type:feature", "size:large"])
    plan = tmp_path / "plan.txt"
    plan.write_text("Just a title\n")
    assert run(gh, "task", "7", "--plan", str(plan)) == 2


def test_task_plan_is_refused_for_a_small_run(gh, tmp_path):
    gh.add(7, labels=["stage:plan", "type:feature", "size:small"])
    plan = tmp_path / "plan.txt"
    plan.write_text("one: One\n")
    assert run(gh, "task", "7", "--plan", str(plan)) == 3


def test_task_done_ticks_tasks_in_order_only(gh):
    body = BODY.replace("- [x] T1", "- [ ] T1")
    gh.add(7, body=body, labels=["stage:build", "type:feature", "size:large"])
    assert run(gh, "task", "7", "--done", "T2") == 3
    assert run(gh, "task", "7", "--done", "T1") == 0
    assert run(gh, "task", "7", "--done", "T1") == 0
    assert [t.done for t in fi.parse_delivery(sections(gh, 7)["Delivery"]).tasks] == [True, False]
    assert run(gh, "task", "7", "--done", "T9") == 2


# claim and release


def test_claim_holds_a_free_issue(gh):
    gh.add(7, labels=["stage:build"])
    assert run(gh, "claim", "7", "--session", "mac-20261020-1200") == 0
    assert "claimed" in gh.issues[7]["labels"]
    assert fi.claim_holder(gh.issues[7]["comments"]) == "mac-20261020-1200"


def test_claim_refuses_an_issue_held_by_another_session(gh):
    gh.add(7, labels=["stage:build", "claimed"], comments=["Factory: claimed by session `a`."])
    assert run(gh, "claim", "7", "--session", "b") == 3
    assert fi.claim_holder(gh.issues[7]["comments"]) == "a"


def test_takeover_moves_the_claim(gh):
    gh.add(7, labels=["stage:build", "claimed"], comments=["Factory: claimed by session `a`."])
    assert run(gh, "claim", "7", "--session", "b", "--takeover") == 0
    assert fi.claim_holder(gh.issues[7]["comments"]) == "b"


def test_claim_loses_a_race_to_an_earlier_claim(gh):
    class Racing(FakeGitHub):
        def comment(self, number, text):
            self.issues[number]["comments"].append("Factory: claimed by session `other`.")
            super().comment(number, text)

    racing = Racing()
    racing.add(7, labels=["stage:build"])
    assert run(racing, "claim", "7", "--session", "mine") == 3
    assert fi.claim_holder(racing.issues[7]["comments"]) == "other"


def test_release_ends_this_sessions_claim(gh):
    gh.add(7, labels=["stage:build", "claimed"], comments=["Factory: claimed by session `a`."])
    assert run(gh, "release", "7", "--session", "a") == 0
    assert "claimed" not in gh.issues[7]["labels"]
    assert fi.claim_holder(gh.issues[7]["comments"]) is None


def test_release_refuses_another_sessions_claim_without_takeover(gh):
    gh.add(7, labels=["stage:build", "claimed"], comments=["Factory: claimed by session `a`."])
    assert run(gh, "release", "7", "--session", "b") == 3
    assert run(gh, "release", "7", "--session", "b", "--takeover") == 0
    assert fi.claim_holder(gh.issues[7]["comments"]) is None


def test_claim_rejects_a_session_id_with_spaces(gh):
    gh.add(7, labels=["stage:build"])
    assert run(gh, "claim", "7", "--session", "my session") == 2


# status


def test_status_reports_the_run_and_its_next_task(gh, capsys):
    gh.add(7, labels=["stage:build", "type:feature", "size:large"])
    assert run(gh, "status", "7") == 0
    status = json.loads(capsys.readouterr().out)
    assert status["stage"] == "build"
    assert status["branch"] == "int/7-add-the-thing"
    assert status["next_task"] == "T2"
    assert status["problems"] == []


@pytest.mark.parametrize(
    ("labels", "body", "problem"),
    [
        (["stage:build", "stage:ship", "type:feature", "size:large"], BODY, "more than one stage label"),
        (["stage:build", "type:feature", "size:small"], "## Request\n\n> x\n", "no delivery branch"),
        (["stage:build", "type:feature", "size:large", "claimed"], BODY, "the claimed label and the claim comments"),
        (["stage:build", "type:fix", "size:large"], BODY, "title does not start with the fix prefix"),
        (["stage:spec"], BODY, "no type label after define"),
        (["stage:plan", "type:fix", "size:small"], BODY, "a small run in stage plan"),
        (["stage:build", "type:feature", "size:large"], "stray text\n" + BODY, "body: text before the first section"),
        (
            ["stage:build", "type:feature", "size:large"],
            BODY.replace("- [ ] T2", "- [x] T2").replace("- [x] T1", "- [ ] T1"),
            "out of order",
        ),
    ],
)
def test_status_reports_problems(gh, capsys, labels, body, problem):
    gh.add(7, labels=labels, body=body)
    run(gh, "status", "7")
    problems = json.loads(capsys.readouterr().out)["problems"]
    assert any(problem in p for p in problems), problems


def test_status_lists_label_and_stage_problems_before_a_body_error(gh, capsys):
    gh.add(7, labels=["stage:build"], body="stray\n## Request\n\n> x\n")
    run(gh, "status", "7")
    problems = json.loads(capsys.readouterr().out)["problems"]
    expected = ["no type label after define", "no size label after define", "body", "no delivery branch"]
    assert [problem.split(":")[0] for problem in problems] == expected


def test_queue_lists_factory_issues_owner_first_then_furthest_along(gh, capsys):
    gh.add(1, labels=["stage:define"])
    gh.add(2, labels=["bug"])
    gh.add(3, labels=["stage:build"])
    gh.add(4, labels=["stage:triage", "needs:owner"])
    run(gh, "status")
    assert [row["number"] for row in json.loads(capsys.readouterr().out)] == [4, 3, 1]


def test_queue_never_lists_a_content_issue_even_one_waiting_for_the_owner(gh, capsys):
    gh.add(1, labels=["stage:build", "kind:factory"])
    content = ["kind:youtube", "channel:testlab", "youtube-stage:script", "needs:owner"]
    gh.add(2, body="A video.", labels=content, comments=["Factory: needs the owner: Approve the script."])
    run(gh, "status")
    assert [row["number"] for row in json.loads(capsys.readouterr().out)] == [1]


def test_queue_shows_what_each_waiting_run_needs_and_its_pull_request(gh, capsys):
    needs = ["Factory: needs the owner: Approve G1.", "Factory: needs the owner: Review PR #12."]
    gh.add(4, body=BODY.replace("PR: none", "PR: #12"), labels=["stage:ship", "needs:owner"], comments=needs)
    gh.add(5, labels=["stage:build"], comments=["Factory: needs the owner: Answered long ago."])
    run(gh, "status")
    rows = {row["number"]: row for row in json.loads(capsys.readouterr().out)}
    assert (rows[4]["needed"], rows[4]["pr"]) == ("Review PR #12.", 12)
    assert (rows[5]["needed"], rows[5]["pr"]) == (None, None)


def test_queue_shows_the_claim_and_reports_unreadable_runs(gh, capsys):
    gh.add(4, body=BODY.replace("PR: none", "PR: #12") + "- [ ] T3 typed by hand\n", labels=["stage:build", "claimed"])
    gh.add(5, labels=["stage:build", "stage:ship"])
    gh.add(6, labels=["stage:define"])
    run(gh, "status")
    rows = {row["number"]: row for row in json.loads(capsys.readouterr().out)}
    assert (rows[4]["claimed"], rows[6]["claimed"]) == (True, False)
    assert any("unreadable line" in problem for problem in rows[4]["problems"])
    assert any("more than one stage label" in problem for problem in rows[5]["problems"])
    assert rows[6]["problems"] == []


def test_status_shows_the_need_only_while_waiting(gh, capsys):
    gh.add(7, labels=["stage:define", "needs:owner"], comments=["Factory: needs the owner: Approve G1."])
    run(gh, "status", "7")
    assert json.loads(capsys.readouterr().out)["needed"] == "Approve G1."
    gh.edit(7, remove=["needs:owner"])
    run(gh, "status", "7")
    assert json.loads(capsys.readouterr().out)["needed"] is None


# labels


def test_labels_creates_missing_and_updates_changed_labels(gh):
    config = fi.load_config(fi.CONFIG)
    gh.repo_labels = {"type:fix": ("000000", "old"), "bug": ("d73a4a", "Something isn't working")}
    assert run(gh, "labels", "--check") == 1
    assert run(gh, "labels") == 0
    assert all(gh.repo_labels[name] == wanted for name, wanted in config.labels.items())
    assert gh.repo_labels["bug"] == ("d73a4a", "Something isn't working")
    assert run(gh, "labels", "--check") == 0


def backfill_issues(gh):
    gh.add(1, labels=["stage:build"])
    gh.add(2, labels=["stage:define", "kind:factory"])
    gh.add(3, labels=["bug"])
    gh.add(4, labels=["kind:youtube", "channel:testlab", "youtube-stage:script"])


def test_labels_backfill_kind_marks_open_factory_issues_without_it(gh):
    backfill_issues(gh)
    assert run(gh, "labels", "--backfill-kind") == 0
    assert [gh.issues[n]["labels"] for n in (1, 2, 3, 4)] == [
        ["stage:build", "kind:factory"],
        ["stage:define", "kind:factory"],
        ["bug"],
        ["kind:youtube", "channel:testlab", "youtube-stage:script"],
    ]
    assert "kind:factory" in gh.repo_labels


def test_labels_backfill_kind_with_check_only_reports(gh, capsys):
    config = fi.load_config(fi.CONFIG)
    gh.repo_labels = dict(config.labels)
    backfill_issues(gh)
    assert run(gh, "labels", "--check", "--backfill-kind") == 1
    assert "backfill #1" in capsys.readouterr().out
    assert gh.issues[1]["labels"] == ["stage:build"]


def test_labels_without_backfill_kind_leaves_issues_alone(gh):
    backfill_issues(gh)
    assert run(gh, "labels") == 0
    assert gh.issues[1]["labels"] == ["stage:build"]


# body format and config


def test_body_round_trips():
    assert fi.render_body(fi.parse_body(BODY)) == BODY
    delivery = fi.parse_body(BODY)["Delivery"]
    assert fi.render_delivery(fi.parse_delivery(delivery)) == delivery


def test_config_stages_match_the_lifecycle_in_the_factory_rule():
    config = fi.load_config(fi.CONFIG)
    rule = (ROOT / "agentic" / "rules" / "factory.md").read_text()
    lifecycle = rule.split("## Lifecycle", 1)[1].split("\n## ", 1)[0]
    assert re.findall(r"^\| `([a-z]+)` \|", lifecycle, re.MULTILINE) == config.family("stage") == fi.STAGES


def test_load_config_rejects_stages_out_of_lifecycle_order(tmp_path):
    text = fi.CONFIG.read_text()
    swapped = text.replace('"stage:spec"', '"stage:tmp"').replace('"stage:plan"', '"stage:spec"')
    config = tmp_path / "factory.yaml"
    config.write_text(swapped.replace('"stage:tmp"', '"stage:plan"'))
    with pytest.raises(fi.Error):
        fi.load_config(config)
