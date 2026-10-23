"""Tests for agentic/scripts/content_issue.py, against an in-memory GitHub and a tmp channel workspace."""

import json

import content_issue as ci
import pytest
from test_factory_issue import FakeGitHub as FactoryFakeGitHub
from test_youtube_channel import workspace

LABEL = "channel:example-lab"


class FakeGitHub(FactoryFakeGitHub):
    """The factory fake plus GitHub sub-issues."""

    def __init__(self):
        super().__init__()
        self.sub_issues = {}  # parent number -> child numbers

    def add_sub_issue(self, parent, child):
        self.sub_issues.setdefault(parent, []).append(child)


@pytest.fixture
def gh():
    return FakeGitHub()


@pytest.fixture
def channel(tmp_path):
    return workspace(tmp_path)


def run(gh, root, *argv):
    return ci.main(list(argv), gh=gh, root=root)


# new


def test_new_files_a_long_form_video_at_idea_with_its_folder(gh, tmp_path, channel):
    brief = tmp_path / "brief.md"
    brief.write_text("Testers ask what the AI skipped.\n")
    code = run(
        gh, tmp_path, "new", "example", "--type", "long-form", "--title", "What AI skips", "--brief-file", str(brief)
    )
    assert code == 0
    issue = gh.issues[1]
    assert issue["title"] == "What AI skips"
    assert sorted(issue["labels"]) == sorted(["kind:youtube", LABEL, "content-type:long-form", "youtube-stage:idea"])
    assert issue["body"] == "## Brief\n\n> Testers ask what the AI skipped.\n"
    assert issue["comments"] == ["YouTube: filed for channel `example`; stage `idea`."]
    assert (channel / "videos" / "1").is_dir()


def test_new_creates_the_content_labels_and_the_channel_label_on_demand(gh, tmp_path, channel):
    gh.repo_labels["needs:owner"] = ("b60205", "The factory is waiting for the owner")
    assert run(gh, tmp_path, "new", "example", "--type", "short", "--title", "A Short") == 0
    assert gh.repo_labels[LABEL] == ("006b75", "YouTube channel: Example Lab")
    assert gh.repo_labels["kind:youtube"][0] == "ff0000"
    assert {f"youtube-stage:{s}" for s in ci.load_config(ci.CONFIG, ci.FACTORY_CONFIG).stages} <= set(gh.repo_labels)
    assert gh.repo_labels["needs:owner"] == ("b60205", "The factory is waiting for the owner")
    assert gh.issues[1]["body"] == "## Brief\n\n> (empty)\n"


def test_new_refuses_an_invalid_channel_and_files_nothing(gh, tmp_path):
    workspace(tmp_path, guide=False)
    assert run(gh, tmp_path, "new", "example", "--type", "long-form", "--title", "No guide") == 2
    assert gh.issues == {}
    assert gh.repo_labels == {}


# stage and gate


def video(gh, number, stage="idea", kind="long-form", label=LABEL, body="## Brief\n\n> An idea.\n", comments=()):
    labels = ["kind:youtube", label, f"content-type:{kind}", f"youtube-stage:{stage}"]
    gh.add(number, title=f"Video {number}", body=body, labels=labels, comments=comments)


def stage_of(gh, number):
    return [label for label in gh.issues[number]["labels"] if label.startswith("youtube-stage:")]


def test_stage_moves_one_stage_forward_with_a_comment(gh, tmp_path):
    video(gh, 5, stage="research")
    assert run(gh, tmp_path, "stage", "5", "script") == 0
    assert stage_of(gh, 5) == ["youtube-stage:script"]
    assert gh.issues[5]["comments"] == ["YouTube: stage `research` -> `script`."]


@pytest.mark.parametrize(
    ("current", "target"),
    [("research", "demo"), ("script", "research"), ("script", "script"), ("research", "ready")],
)
def test_stage_refuses_skips_and_backward_moves(gh, tmp_path, current, target):
    video(gh, 5, stage=current)
    assert run(gh, tmp_path, "stage", "5", target) == 3
    assert stage_of(gh, 5) == [f"youtube-stage:{current}"]
    assert gh.issues[5]["comments"] == []


@pytest.mark.parametrize(
    ("gate", "current", "target"), [(1, "idea", "research"), (2, "demo", "recording"), (3, "review", "ready")]
)
def test_stage_refuses_to_pass_a_gate_without_the_owners_recorded_yes(gh, tmp_path, gate, current, target):
    video(gh, 5, stage=current, comments=[f"YouTube: gate {gate % 3 + 1} approved."])
    assert run(gh, tmp_path, "stage", "5", target) == 3
    assert stage_of(gh, 5) == [f"youtube-stage:{current}"]


def test_gate_approval_records_the_owners_yes_and_lets_the_video_pass(gh, tmp_path):
    video(gh, 5, stage="demo")
    gh.issues[5]["labels"].append("needs:owner")
    assert run(gh, tmp_path, "gate", "5", "2", "--approve") == 0
    assert gh.issues[5]["comments"] == ["YouTube: gate 2 approved."]
    assert "needs:owner" not in gh.issues[5]["labels"]
    assert run(gh, tmp_path, "stage", "5", "recording") == 0
    assert stage_of(gh, 5) == ["youtube-stage:recording"]


def test_gate_refuses_an_approval_away_from_its_stage(gh, tmp_path):
    video(gh, 5, stage="script")
    assert run(gh, tmp_path, "gate", "5", "2", "--approve") == 3
    assert gh.issues[5]["comments"] == []


def test_gate_request_marks_the_video_waiting_for_the_owner(gh, tmp_path):
    video(gh, 5, stage="idea")
    assert run(gh, tmp_path, "gate", "5", "1", "--request") == 0
    assert "needs:owner" in gh.issues[5]["labels"]
    assert gh.issues[5]["comments"] == ["YouTube: gate 1 needs the owner."]


def test_stage_and_gate_refuse_an_issue_that_is_not_a_video(gh, tmp_path):
    gh.add(5, labels=["kind:factory", "stage:build"])
    assert run(gh, tmp_path, "stage", "5", "research") == 3
    assert run(gh, tmp_path, "gate", "5", "1", "--approve") == 3
    assert gh.issues[5]["comments"] == []


@pytest.mark.parametrize("argv", [["stage", "5", "publish"], ["gate", "5", "4", "--approve"]])
def test_stage_and_gate_reject_an_unknown_stage_or_gate(gh, tmp_path, argv):
    video(gh, 5, stage="idea")
    assert run(gh, tmp_path, *argv) == 2


# Shorts


def test_new_short_cut_from_a_long_form_is_its_sub_issue_and_links_it(gh, tmp_path, channel):
    video(gh, 3, stage="editing")
    assert run(gh, tmp_path, "new", "example", "--type", "short", "--title", "Cut", "--parent", "3") == 0
    assert gh.sub_issues == {3: [4]}
    assert "content-type:short" in gh.issues[4]["labels"]
    assert gh.issues[4]["body"] == "## Brief\n\nCut from long-form #3.\n\n> (empty)\n"
    assert (channel / "videos" / "4").is_dir()


def test_new_independent_short_is_standalone_and_links_its_related_long_form(gh, tmp_path, channel):
    video(gh, 3, stage="ready")
    assert run(gh, tmp_path, "new", "example", "--type", "short", "--title", "Own", "--related", "3") == 0
    assert gh.sub_issues == {}
    assert gh.issues[4]["body"] == "## Brief\n\nRelated long-form: #3.\n\n> (empty)\n"


@pytest.mark.parametrize(
    "parent",
    [
        {"kind": "short"},
        {"label": "channel:other-lab"},
    ],
)
@pytest.mark.parametrize("flag", ["--parent", "--related"])
def test_new_short_refuses_a_link_to_anything_but_a_long_form_of_its_channel(gh, tmp_path, channel, parent, flag):
    video(gh, 3, **parent)
    assert run(gh, tmp_path, "new", "example", "--type", "short", "--title", "Cut", flag, "3") == 3
    assert list(gh.issues) == [3]
    assert gh.sub_issues == {}


def test_new_short_refuses_a_factory_issue_as_its_long_form(gh, tmp_path, channel):
    gh.add(3, labels=["kind:factory", "stage:build"])
    assert run(gh, tmp_path, "new", "example", "--type", "short", "--title", "Cut", "--parent", "3") == 3
    assert list(gh.issues) == [3]


def test_new_long_form_rejects_a_long_form_link(gh, tmp_path, channel):
    video(gh, 3)
    assert run(gh, tmp_path, "new", "example", "--type", "long-form", "--title", "Two", "--parent", "3") == 2
    assert list(gh.issues) == [3]


# status


def status(gh, root, capsys, *argv):
    assert run(gh, root, "status", *argv) == 0
    return json.loads(capsys.readouterr().out)


def test_status_resumes_a_video_at_its_stage(gh, tmp_path, capsys, channel):
    video(gh, 3)
    video(gh, 4, stage="idea", kind="short", body="## Brief\n\nCut from long-form #3.\n\n> A cut.\n")
    gh.issues[4]["labels"].append("needs:owner")
    assert status(gh, tmp_path, capsys, "4", "--channel", "example") == {
        "number": 4,
        "title": "Video 4",
        "state": "OPEN",
        "channel": "example-lab",
        "type": "short",
        "stage": "idea",
        "next": "research",
        "gate": 1,
        "approved": [],
        "waiting": True,
        "long_form": 3,
        "parent": 3,
        "folder": "videos/4",
    }


def test_status_shows_an_approved_gate_and_a_related_long_form(gh, tmp_path, capsys):
    body = "## Brief\n\nRelated long-form: #3.\n\n> Own.\n"
    video(gh, 4, stage="idea", kind="short", body=body, comments=["YouTube: gate 1 approved."])
    row = status(gh, tmp_path, capsys, "4")
    assert (row["gate"], row["approved"], row["waiting"]) == (None, [1], False)
    assert (row["long_form"], row["parent"]) == (3, None)


def test_status_refuses_a_video_of_another_channel(gh, tmp_path, channel):
    video(gh, 4, label="channel:other-lab")
    assert run(gh, tmp_path, "status", "4", "--channel", "example") == 3


def test_status_lists_the_channels_open_videos_waiting_for_the_owner_first(gh, tmp_path, capsys, channel):
    video(gh, 1, stage="script")
    video(gh, 2, stage="idea")
    video(gh, 3, stage="review")
    video(gh, 4, stage="demo", label="channel:other-lab")
    gh.add(5, labels=["kind:factory", "stage:build", "needs:owner"])
    gh.issues[2]["labels"].append("needs:owner")
    rows = status(gh, tmp_path, capsys, "--channel", "example")
    assert [row["number"] for row in rows] == [2, 3, 1]
    assert rows[0] == {"number": 2, "title": "Video 2", "type": "long-form", "stage": "idea", "waiting": True}


def test_gate_request_after_the_approval_changes_nothing(gh, tmp_path):
    video(gh, 5, stage="idea", comments=["YouTube: gate 1 approved."])
    assert run(gh, tmp_path, "gate", "5", "1", "--request") == 0
    assert "needs:owner" not in gh.issues[5]["labels"]
    assert gh.issues[5]["comments"] == ["YouTube: gate 1 approved."]


def test_config_holds_the_agreed_stages_and_gates():
    config = ci.load_config(ci.CONFIG, ci.FACTORY_CONFIG)
    assert config.stages == [
        "idea", "research", "script", "demo", "recording", "editing", "packaging", "review", "ready"
    ]  # fmt: skip
    assert config.gates == {1: "idea", 2: "demo", 3: "review"}
