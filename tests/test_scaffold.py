"""Tests for build-video-demo's scaffold.py, through main(argv, root, gh) with a fake GitHub."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from test_youtube_channel import CONFIG, edited, workspace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agentic/skills/content/build-video-demo/scripts"))
import scaffold

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agentic/skills/content/research-video/scripts"))
import evidence

REPO = CONFIG["demos"]["repo"]
ISSUE_URL = "https://github.com/example-org/aksa/issues/42"
LINK = f"https://github.com/{REPO}/tree/main/42-mocked-tests"
PROVES = "A test that mocks the function under test passes even when the code is broken."
SKILL = "check-test-can-fail"
RULES = [
    "Before you call a test done, name the change to the code that would make it fail.",
    "Never mock the unit under test; mock only what it talks to.",
]
KIT = ["--skill", SKILL, "--rule", RULES[0], "--rule", RULES[1]]
ARGV = ["example", "42", "--slug", "mocked-tests", "--proves", PROVES, *KIT]


def claim(number, found=True):
    url, quote = f"https://example.com/source-{number}", f"Quote {number} from the source page."
    return {
        "id": f"C{number}",
        "claim": f"Claim {number}.",
        "url": url,
        "quote": quote,
        "link": evidence.fragment_link(url, quote),
        "found": found,
        "checked": "2026-10-23T10:00:00+00:00",
    }


CITATIONS = [claim(1), claim(2)]


@pytest.fixture(autouse=True)
def no_outer_git(monkeypatch):
    """Under the pre-commit hook, GIT_* variables point git at the aksa repository."""
    for name in [n for n in os.environ if n.startswith("GIT_")]:
        monkeypatch.delenv(name)


class FakeGitHub:
    """The GitHub layer of scaffold.py: it only reads; there is no create to fake."""

    def __init__(self, repos=(REPO,), labels=("kind:youtube", "channel:example-lab")):
        self.repos = set(repos)
        self.labels = list(labels)

    def repo_exists(self, repo):
        return repo in self.repos

    def issue_link(self, number):
        return {"title": "Your AI tests pass. Are they testing anything?", "url": ISSUE_URL, "labels": self.labels}


def clone(root, git=True):
    path = root / ".projects" / "content" / CONFIG["demos"]["path"]
    path.mkdir(parents=True)
    if git:
        subprocess.run(["git", "init", "--quiet", str(path)], check=True)
    return path


def citations(root, claims=CITATIONS):
    folder = root / ".projects" / "content" / "yt-example" / "videos" / "42"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "citations.json").write_text(json.dumps(claims))


@pytest.fixture
def root(tmp_path):
    workspace(tmp_path)
    citations(tmp_path)
    return tmp_path


def test_scaffold_creates_the_readme_demo_tests_and_tape(root):
    folder = clone(root) / "42-mocked-tests"
    assert scaffold.main(ARGV, root=root, gh=FakeGitHub()) == 0
    for name in ["README.md", "demo.tape", "demo/.gitkeep", "tests/.gitkeep", ".gitignore"]:
        assert (folder / name).is_file(), name
    readme = (folder / "README.md").read_text()
    for text in ["# Your AI tests pass. Are they testing anything?", PROVES, "MIT", "python -m pytest"]:
        assert text in readme, text
    assert "{{" not in readme


def test_the_readme_links_the_channel_and_the_folder_never_the_private_issue(root):
    folder = clone(root) / "42-mocked-tests"
    scaffold.main(ARGV, root=root, gh=FakeGitHub())
    readme = (folder / "README.md").read_text()
    assert f"[{CONFIG['name']}]({CONFIG['url']})" in readme
    assert LINK in readme
    assert scaffold.VIDEO_PENDING in readme.splitlines()
    assert ISSUE_URL not in readme and "/issues/" not in readme


def test_the_readme_lists_each_citation_with_its_quote_and_link(root):
    folder = clone(root) / "42-mocked-tests"
    scaffold.main(ARGV, root=root, gh=FakeGitHub())
    readme = (folder / "README.md").read_text()
    for item in CITATIONS:
        assert f'{item["claim"]} "{item["quote"]}" ([source]({item["link"]}))' in readme


@pytest.mark.parametrize("claims", [None, [claim(1), claim(2, found=False)], [claim(1) | {"quote": "Edited."}]])
def test_citations_missing_or_not_verified_are_refused(root, capsys, claims):
    path = clone(root)
    video = root / ".projects" / "content" / "yt-example" / "videos" / "42"
    if claims is None:
        (video / "citations.json").unlink()
    else:
        citations(root, claims)
    assert scaffold.main(ARGV, root=root, gh=FakeGitHub()) == 3
    assert "citations" in capsys.readouterr().err
    assert not (path / "42-mocked-tests").exists()


def test_scaffold_creates_the_ai_kit_with_the_rules_a_skill_and_a_scripts_folder(root):
    kit = clone(root) / "42-mocked-tests" / "ai-kit"
    assert scaffold.main(ARGV, root=root, gh=FakeGitHub()) == 0
    rules = (kit / "AGENTS.md").read_text()
    assert all(f"- {rule}" in rules for rule in RULES)
    assert "Your AI tests pass. Are they testing anything?" in rules and "CLAUDE.md" in rules
    skill = (kit / "skills" / SKILL / "SKILL.md").read_text()
    assert skill.startswith(f"---\nname: {SKILL}\ndescription: Use ")
    assert all(rule in skill for rule in RULES)
    assert (kit / "scripts" / ".gitkeep").is_file()
    assert "{{" not in rules + skill


def test_the_kit_skill_frontmatter_is_valid_yaml_for_a_title_with_a_colon(root):
    kit = clone(root) / "42-mocked-tests" / "ai-kit"
    gh = FakeGitHub()
    gh.issue_link = lambda number: {"title": "Spot the Bug: This AI Test Passes", "labels": gh.labels}
    assert scaffold.main(ARGV, root=root, gh=gh) == 0
    front = (kit / "skills" / SKILL / "SKILL.md").read_text().split("---\n")[1]
    data = yaml.safe_load(front)
    assert data["name"] == SKILL and data["description"].startswith("Use after")


def test_the_readme_shows_how_to_use_the_kit_with_an_ai_agent(root):
    folder = clone(root) / "42-mocked-tests"
    scaffold.main(ARGV, root=root, gh=FakeGitHub())
    readme = (folder / "README.md").read_text()
    assert "## Use it with your AI agent" in readme
    assert f"{LINK}/ai-kit" in readme
    assert f"https://raw.githubusercontent.com/{REPO}/main/42-mocked-tests/ai-kit/AGENTS.md" in readme
    assert f"cp -r ai-kit/skills/{SKILL} .claude/skills/" in readme


@pytest.mark.parametrize(
    "kit",
    [
        ["--skill", "check", "--rule", "A rule."],
        ["--skill", "Check_Tests", "--rule", "A rule."],
        ["--skill", SKILL, "--rule", "  "],
    ],
)
def test_a_kit_skill_not_verb_object_or_a_blank_rule_is_refused(root, capsys, kit):
    path = clone(root)
    argv = ["example", "42", "--slug", "mocked-tests", "--proves", PROVES, *kit]
    assert scaffold.main(argv, root=root, gh=FakeGitHub()) == 2
    err = capsys.readouterr().err
    assert "skill" in err or "rule" in err
    assert not (path / "42-mocked-tests").exists()


def test_the_tape_records_the_folder_at_the_channel_terminal_size(root):
    folder = clone(root) / "42-mocked-tests"
    scaffold.main(ARGV, root=root, gh=FakeGitHub())
    tape = (folder / "demo.tape").read_text()
    for line in [
        "Output demo.mp4",
        "# scene",
        'Set FontFamily "Menlo"',
        "Set FontSize 30",
        "Set Width 1920",
        "Set Height 1080",
    ]:
        assert line in tape, line
    assert "{{" not in tape
    assert "*.mp4" in (folder / ".gitignore").read_text().splitlines()


def test_the_tape_spaces_its_steps_and_shows_each_code_change(root):
    # Owner, second gate 3 of #38: a blank line between terminal steps; a mutation shows its changed line. Third
    # gate 3: the blank line comes before each "# comment" step, none between a comment and its command.
    folder = clone(root) / "42-mocked-tests"
    scaffold.main(ARGV, root=root, gh=FakeGitHub())
    tape = (folder / "demo.tape").read_text()
    setup = next(line for line in tape.splitlines() if line.startswith('Type "setopt'))
    assert "c=1 && zshaddhistory() { [[ $1 == '#'* ]] && c=1 || c=0; }" in setup
    assert "precmd() { (( c )) || echo; }" in setup
    assert "prints the line before and after" in tape


def test_the_readme_says_the_demo_is_realistic_code(root):
    # Owner, second gate 3 of #38: examples close to real-world code, not a toy function.
    folder = clone(root) / "42-mocked-tests"
    scaffold.main(ARGV, root=root, gh=FakeGitHub())
    assert "a slice of a real service" in (folder / "README.md").read_text()


def test_scaffold_prints_the_description_link(root, capsys):
    clone(root)
    scaffold.main(ARGV, root=root, gh=FakeGitHub())
    assert capsys.readouterr().out.strip().splitlines()[-1] == LINK


def test_an_existing_folder_is_refused_and_left_unchanged(root):
    folder = clone(root) / "42-mocked-tests"
    folder.mkdir()
    (folder / "README.md").write_text("the owner's")
    assert scaffold.main(ARGV, root=root, gh=FakeGitHub()) == 3
    assert (folder / "README.md").read_text() == "the owner's"
    assert not (folder / "demo.tape").exists()


def test_a_missing_clone_is_refused(root, capsys):
    assert scaffold.main(ARGV, root=root, gh=FakeGitHub()) == 3
    assert "clone" in capsys.readouterr().err


def test_a_clone_that_is_not_a_git_repository_is_refused(root, capsys):
    path = clone(root, git=False)
    assert scaffold.main(ARGV, root=root, gh=FakeGitHub()) == 3
    assert "git repository" in capsys.readouterr().err
    assert list(path.iterdir()) == []


def test_a_demo_repository_missing_on_github_is_refused_for_the_owner(root, capsys):
    path = clone(root)
    assert scaffold.main(ARGV, root=root, gh=FakeGitHub(repos=())) == 3
    assert "owner" in capsys.readouterr().err
    assert not (path / "42-mocked-tests").exists()


def test_an_issue_of_another_channel_is_refused(root):
    path = clone(root)
    assert scaffold.main(ARGV, root=root, gh=FakeGitHub(labels=["kind:factory"])) == 2
    assert not (path / "42-mocked-tests").exists()


@pytest.mark.parametrize("slug", ["Mocked_Tests", "../escape", "mocked tests"])
def test_a_bad_slug_is_refused(root, slug):
    clone(root)
    assert scaffold.main(["example", "42", "--slug", slug, "--proves", PROVES, *KIT], root=root, gh=FakeGitHub()) == 2


def test_a_channel_without_demo_settings_is_refused(tmp_path, capsys):
    workspace(tmp_path, config=edited(CONFIG, "demos"))
    assert scaffold.main(ARGV, root=tmp_path, gh=FakeGitHub()) == 2
    assert "demos" in capsys.readouterr().err
