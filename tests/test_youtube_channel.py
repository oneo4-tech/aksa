"""Tests for agentic/scripts/youtube_channel.py, against a workspace in a tmp root."""

import os
import re
import subprocess

import pytest
import yaml
import youtube_channel as yc

CONFIG = {
    "name": "Example Lab",
    "url": "https://example.com/channel/example-lab",
    "voice": {"id": "Puck", "style": "warm and conversational", "pace": 0.92},
    "palette": {"background": "#000000", "syntax": "#FF3B3B", "name": "#FFFFFF", "suffix": "#00E5FF"},
    "loudness": {"lufs": -14, "true_peak": -1.0},
    "music_db": -24,
    "cadence": {"long_form_per_week": 1, "shorts_per_week": 2, "owner_hours_per_week": 5},
    "labels": {"channel": "channel:example-lab"},
    "pronunciation": {"pytest": "pie test"},
    "banned_phrases": ["in this video"],
    "title_max": 60,
}


@pytest.fixture(autouse=True)
def no_outer_git(monkeypatch):
    """Under the pre-commit hook, GIT_* variables point git at the aksa repository."""
    for name in [n for n in os.environ if n.startswith("GIT_")]:
        monkeypatch.delenv(name)


def style_guide(sections=yc.SECTIONS):
    return "# Style guide\n\n" + "".join(f"## {name}\n\nRules for {name.lower()}.\n\n" for name in sections)


def workspace(root, config=CONFIG, guide=None):
    path = root / ".projects" / "content" / "yt-example"
    path.mkdir(parents=True, exist_ok=True)
    if config is not None:
        (path / "channel.yaml").write_text(yaml.safe_dump(config))
    if guide is not False:
        (path / "style-guide.md").write_text(guide or style_guide())
    return path


def edited(config, dotted, value=None):
    """A deep copy of config with one dotted field set to value, or removed when value is None."""
    result = yaml.safe_load(yaml.safe_dump(config))
    *parents, last = dotted.split(".")
    node = result
    for key in parents:
        node = node[key]
    if value is None:
        del node[last]
    else:
        node[last] = value
    return result


def test_load_returns_config_and_style_sections(tmp_path):
    workspace(tmp_path)
    channel = yc.load("example", root=tmp_path)
    assert channel.config["voice"]["id"] == "Puck"
    assert channel.config["labels"]["channel"] == "channel:example-lab"
    assert list(channel.style) == yc.SECTIONS
    assert channel.style["Audio"] == "Rules for audio."
    assert channel.workspace == tmp_path / ".projects" / "content" / "yt-example"


@pytest.mark.parametrize(
    "field",
    [
        "name",
        "url",
        "voice",
        "voice.id",
        "voice.pace",
        "palette.suffix",
        "loudness.true_peak",
        "music_db",
        "cadence.shorts_per_week",
        "cadence.owner_hours_per_week",
        "labels.channel",
        "pronunciation",
        "banned_phrases",
        "title_max",
    ],
)
def test_load_names_a_missing_field(tmp_path, field):
    workspace(tmp_path, config=edited(CONFIG, field))
    with pytest.raises(yc.ChannelError, match=rf"\b{re.escape(field)}\b.*missing"):
        yc.load("example", root=tmp_path)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("name", ""),
        ("url", "example.com/no-scheme"),
        ("voice.pace", "fast"),
        ("palette.background", "black"),
        ("loudness.lufs", True),
        ("cadence.long_form_per_week", 1.5),
        ("cadence.shorts_per_week", -1),
        ("cadence.owner_hours_per_week", 0),
        ("labels.channel", "example-lab"),
        ("pronunciation", ["pytest"]),
        ("banned_phrases", "in this video"),
        ("title_max", 0),
    ],
)
def test_load_names_an_invalid_field(tmp_path, field, value):
    workspace(tmp_path, config=edited(CONFIG, field, value))
    with pytest.raises(yc.ChannelError, match=rf"\b{re.escape(field)}\b"):
        yc.load("example", root=tmp_path)


def test_load_names_every_bad_field_at_once(tmp_path):
    config = edited(edited(CONFIG, "voice.id"), "title_max", "long")
    workspace(tmp_path, config=config)
    with pytest.raises(yc.ChannelError) as error:
        yc.load("example", root=tmp_path)
    assert "voice.id" in str(error.value) and "title_max" in str(error.value)


def test_load_refuses_a_missing_config(tmp_path):
    workspace(tmp_path, config=None)
    with pytest.raises(yc.ChannelError, match="channel.yaml"):
        yc.load("example", root=tmp_path)


def test_load_refuses_a_missing_style_guide(tmp_path):
    workspace(tmp_path, guide=False)
    with pytest.raises(yc.ChannelError, match="style-guide.md.*missing"):
        yc.load("example", root=tmp_path)


def test_load_names_each_missing_style_section(tmp_path):
    workspace(tmp_path, guide=style_guide([s for s in yc.SECTIONS if s not in {"Captions", "Gate 2 checklist"}]))
    with pytest.raises(yc.ChannelError) as error:
        yc.load("example", root=tmp_path)
    assert "Captions" in str(error.value) and "Gate 2 checklist" in str(error.value)


def test_load_refuses_a_bad_channel_name(tmp_path):
    with pytest.raises(yc.ChannelError, match="channel name"):
        yc.load("../escape", root=tmp_path)


def ignored(repo, path):
    return subprocess.run(["git", "-C", str(repo), "check-ignore", "-q", path], check=False).returncode == 0


def test_init_makes_a_git_workspace_that_ignores_media(tmp_path):
    (tmp_path / ".projects").mkdir()
    path = yc.init("example", root=tmp_path)
    assert (path / ".git").is_dir() and (path / "videos").is_dir()
    for media in ["videos/12/final.mp4", "videos/12/scene-1.wav", "videos/12/thumb.png"]:
        assert ignored(path, media), media
    for text in ["videos/12/script.md", "videos/12/citations.json", "branding/logo.svg", "style-guide.md"]:
        assert not ignored(path, text), text


def test_init_ignores_git_variables_inherited_from_a_hook(tmp_path, monkeypatch):
    outer = tmp_path / "outer"
    subprocess.run(["git", "init", "--quiet", str(outer)], check=True)
    monkeypatch.setenv("GIT_DIR", str(outer / ".git"))
    monkeypatch.setenv("GIT_INDEX_FILE", str(outer / ".git" / "index"))
    (tmp_path / ".projects").mkdir()
    path = yc.init("example", root=tmp_path)
    monkeypatch.delenv("GIT_DIR")
    monkeypatch.delenv("GIT_INDEX_FILE")
    assert (path / ".git").is_dir()
    bare = subprocess.run(["git", "-C", str(outer), "config", "core.bare"], capture_output=True, text=True, check=True)
    assert bare.stdout.strip() == "false"


def test_init_is_idempotent_and_keeps_owner_rules(tmp_path):
    (tmp_path / ".projects").mkdir()
    path = yc.init("example", root=tmp_path)
    gitignore = path / ".gitignore"
    gitignore.write_text(gitignore.read_text() + "drafts/\n")
    yc.init("example", root=tmp_path)
    lines = gitignore.read_text().splitlines()
    assert "drafts/" in lines
    assert lines.count("*.mp4") == 1


def test_init_refuses_without_the_projects_link(tmp_path):
    with pytest.raises(yc.ChannelError, match=r"\.projects"):
        yc.init("example", root=tmp_path)


def test_cli_check_reports_ok(tmp_path, capsys):
    workspace(tmp_path)
    assert yc.main(["check", "example"], root=tmp_path) == 0
    assert "ok" in capsys.readouterr().out


def test_cli_check_exits_2_naming_the_field(tmp_path, capsys):
    workspace(tmp_path, config=edited(CONFIG, "voice.id"))
    assert yc.main(["check", "example"], root=tmp_path) == 2
    assert "voice.id" in capsys.readouterr().err


def test_cli_init_creates_the_workspace(tmp_path):
    (tmp_path / ".projects").mkdir()
    assert yc.main(["init", "example"], root=tmp_path) == 0
    assert (tmp_path / ".projects" / "content" / "yt-example" / ".gitignore").is_file()


# Writing checks every specialist shares: banned phrases and title length

PHRASES = {"banned_phrases": ["in this video", "let's dive in", "game-changer", "Delve", "unlock"]}


@pytest.mark.parametrize(
    ("text", "found"),
    [
        ("In This Video we break a test.", ["in this video"]),
        ("Let’s dive in and delve into it.", ["let's dive in", "Delve"]),
        ("A game-changer? No.", ["game-changer"]),
        ("in  this\nvideo", ["in this video"]),
    ],
)
def test_banned_phrases_finds_each_phrase_ignoring_case_spacing_and_curly_quotes(text, found):
    assert yc.banned_phrases(text, PHRASES) == found


@pytest.mark.parametrize("text", ["The key unlocks nothing.", "Delvers dig.", "Video in this format.", ""])
def test_banned_phrases_matches_whole_words_only(text):
    assert yc.banned_phrases(text, PHRASES) == []


@pytest.mark.parametrize(
    ("title", "ok"),
    [("x" * 60, True), ("x" * 61, False), ("Spot the Bug: a test that tests nothing", True), ("   ", False)],
)
def test_title_ok_allows_at_most_title_max_characters(title, ok):
    assert yc.title_ok(title, {"title_max": 60}) is ok
