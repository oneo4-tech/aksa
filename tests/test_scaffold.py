"""Tests for build-video-demo's scaffold.py, through main(argv, root, gh) with a fake GitHub."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from test_youtube_channel import CONFIG, edited, workspace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agentic/skills/content/build-video-demo/scripts"))
import scaffold

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agentic/skills/content/research-video/scripts"))
import evidence

REPO = CONFIG["demos"]["repo"]
ISSUE_URL = "https://github.com/example-org/aksa/issues/42"
LINK = f"https://github.com/{REPO}/tree/main/42-mocked-tests"
PROVES = "A test that mocks the function under test passes even when the code is broken."
ARGV = ["example", "42", "--slug", "mocked-tests", "--proves", PROVES]


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


def test_the_tape_records_the_folder_at_the_channel_terminal_size(root):
    folder = clone(root) / "42-mocked-tests"
    scaffold.main(ARGV, root=root, gh=FakeGitHub())
    tape = (folder / "demo.tape").read_text()
    for line in ["Output demo.mp4", 'Set FontFamily "Menlo"', "Set FontSize 30", "Set Width 1920", "Set Height 1080"]:
        assert line in tape, line
    assert "{{" not in tape
    assert "*.mp4" in (folder / ".gitignore").read_text().splitlines()


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
    assert scaffold.main(["example", "42", "--slug", slug, "--proves", PROVES], root=root, gh=FakeGitHub()) == 2


def test_a_channel_without_demo_settings_is_refused(tmp_path, capsys):
    workspace(tmp_path, config=edited(CONFIG, "demos"))
    assert scaffold.main(ARGV, root=tmp_path, gh=FakeGitHub()) == 2
    assert "demos" in capsys.readouterr().err
