"""Tests for the package-video skill's scripts/package.py, through main(argv, root) with a tmp workspace."""

import json
import os
import sys
from pathlib import Path

import pytest
from test_scaffold import CITATIONS, FakeGitHub, claim, clone
from test_youtube_channel import CONFIG, workspace

# A script serving one skill stays in the skill (components.md), outside the pytest pythonpath.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agentic/skills/content/package-video/scripts"))
import package
import scaffold

LONG, SHORT = 14, 15
FPS = 30
DEMO = "https://github.com/example-org/example-demos/tree/main/14-mocked-tests"
LONG_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
SHORT_URL = "https://www.youtube.com/shorts/abcDEF12345"
# Scene starts 0, 25, 60, 150, and 225 s; the video ends at 300 s.
SECONDS = [25, 35, 90, 75, 75]
CHAPTERS = [
    {"scene": 1, "title": "Two green tests"},
    {"scene": 2, "title": "The code"},
    {"scene": 3, "title": "Testing the mock"},
    {"scene": 5, "title": "Break the code"},
]


@pytest.fixture(autouse=True)
def no_outer_git(monkeypatch):
    """Under the pre-commit hook, GIT_* variables point git at the aksa repository."""
    for name in [n for n in os.environ if n.startswith("GIT_")]:
        monkeypatch.delenv(name)


def metadata(**fields):
    base = {
        "title": "Spot the Bug: This AI Test Passes and Tests Nothing",
        "hook": "Two AI-written unit tests pass, and neither can fail.",
        "chapters": CHAPTERS,
        "tags": ["software testing", "ai testing", "pytest", "unit tests", "mutation testing"],
        "hashtags": ["#softwaretesting", "#ai", "#pytest"],
        "paid_promotion": None,
    }
    return base | fields


def video(root, number=LONG, kind="long-form", meta=None, seconds=SECONDS, demo=True, citations=CITATIONS):
    """Write a packaged-ready video folder: script, rendered scenes, demo, citations, metadata."""
    folder = workspace(root) / "videos" / str(number)
    (folder / "render").mkdir(parents=True, exist_ok=True)
    scenes = [{"heading": f"Scene {i}", "say": "Words."} for i in range(1, len(seconds) + 1)]
    (folder / "script.json").write_text(json.dumps({"title": "Spot the Bug", "type": kind, "scenes": scenes}))
    rendered = [{"scene": i, "frames": s * FPS, "seconds": s} for i, s in enumerate(seconds, 1)]
    (folder / "render" / "scenes.json").write_text(json.dumps({"type": kind, "fps": FPS, "scenes": rendered}))
    if demo:
        link = {"folder": "14-mocked-tests", "link": DEMO, "proves": "It passes.", "pushed": True}
        (folder / "demo.json").write_text(json.dumps(link))
    if citations is not None:
        (folder / "citations.json").write_text(json.dumps(citations))
    (folder / "metadata.json").write_text(json.dumps(meta if meta is not None else metadata()))
    return folder


def short(root, related_url=LONG_URL, **fields):
    """A Short related to long-form LONG, which is packaged and, with related_url, published."""
    long_form = video(root)
    if related_url:
        (long_form / "packaging.json").write_text(json.dumps({"video_url": related_url}))
    meta = metadata(chapters=[], related=LONG) | fields
    return video(root, SHORT, "short", meta, seconds=[10, 15, 20])


def run(root, number=LONG, *extra):
    return package.main(["example", str(number), *extra], root=root)


def packaged(folder):
    return json.loads((folder / "packaging.json").read_text())


def test_a_long_form_description_has_hook_chapters_demo_sources_disclosure_and_hashtags(tmp_path):
    folder = video(tmp_path)
    assert run(tmp_path) == 0
    sources = "\n".join(f"- {c['claim']} {c['link']}" for c in CITATIONS)
    assert (folder / "description.md").read_text() == (
        "Two AI-written unit tests pass, and neither can fail.\n\n"
        "00:00 Two green tests\n00:25 The code\n01:00 Testing the mock\n03:45 Break the code\n\n"
        f"Code: {DEMO}\n\n"
        f"Sources:\n{sources}\n\n"
        "Narration uses a synthetic AI voice.\nNo paid promotion.\n\n"
        "#softwaretesting #ai #pytest\n"
    )
    data = packaged(folder)
    assert data["title"] == metadata()["title"]
    assert data["description"] == (folder / "description.md").read_text()
    assert data["tags"] == metadata()["tags"]
    assert data["chapters"][1] == {"at": "00:25", "title": "The code"}
    assert data["paid_promotion"] is False and data["video_url"] is None


def test_chapters_past_an_hour_show_hours(tmp_path):
    chapters = [{"scene": 1, "title": "Start"}, {"scene": 2, "title": "Middle"}, {"scene": 4, "title": "End"}]
    folder = video(tmp_path, meta=metadata(chapters=chapters), seconds=[25, 35, 3600, 75])
    assert run(tmp_path) == 0
    assert "1:01:00 End" in (folder / "description.md").read_text()


@pytest.mark.parametrize(
    ("chapters", "problem"),
    [
        (CHAPTERS[1:], "first chapter must start at 00:00"),
        (CHAPTERS[:2], "at least 3 chapters"),
        ([CHAPTERS[0], CHAPTERS[2], CHAPTERS[1]], "ascending"),
        ([CHAPTERS[0], CHAPTERS[1], CHAPTERS[1]], "ascending"),
        ([CHAPTERS[0], {"scene": 9, "title": "Gone"}, CHAPTERS[2]], "scene 9"),
    ],
)
def test_invalid_chapters_are_refused_naming_the_rule(tmp_path, capsys, chapters, problem):
    folder = video(tmp_path, meta=metadata(chapters=chapters))
    assert run(tmp_path) == 3
    assert problem in capsys.readouterr().err
    assert not (folder / "packaging.json").exists()


def test_a_chapter_shorter_than_ten_seconds_is_refused(tmp_path, capsys):
    chapters = [CHAPTERS[0], CHAPTERS[1], CHAPTERS[2], {"scene": 5, "title": "Tail"}]
    video(tmp_path, meta=metadata(chapters=chapters), seconds=[25, 9, 90, 75, 8])
    assert run(tmp_path) == 3
    err = capsys.readouterr().err
    assert "'The code' is 9 s" in err and "'Tail' is 8 s" in err


def test_a_title_over_title_max_is_refused(tmp_path, capsys):
    video(tmp_path, meta=metadata(title="Spot the Bug: " + "x" * (CONFIG["title_max"] - 13)))
    assert run(tmp_path) == 3
    assert f"title: over {CONFIG['title_max']} characters" in capsys.readouterr().err


def test_a_title_of_exactly_title_max_passes(tmp_path):
    video(tmp_path, meta=metadata(title="Spot the Bug: " + "x" * (CONFIG["title_max"] - 14)))
    assert run(tmp_path) == 0


@pytest.mark.parametrize("field", ["title", "hook"])
def test_a_blank_title_or_hook_is_refused(tmp_path, capsys, field):
    video(tmp_path, meta=metadata(**{field: "  "}))
    assert run(tmp_path) == 3
    assert f"{field}: empty" in capsys.readouterr().err


@pytest.mark.parametrize("field", ["title", "hook"])
def test_a_banned_phrase_in_the_title_or_hook_is_refused(tmp_path, capsys, field):
    video(tmp_path, meta=metadata(**{field: "In this video the AI test passes"}))
    assert run(tmp_path) == 3
    assert f"{field}: banned phrase 'in this video'" in capsys.readouterr().err


def test_a_banned_phrase_in_a_chapter_title_is_refused(tmp_path, capsys):
    chapters = [CHAPTERS[0] | {"title": "In this video"}, *CHAPTERS[1:]]
    video(tmp_path, meta=metadata(chapters=chapters))
    assert run(tmp_path) == 3
    assert "banned phrase 'in this video'" in capsys.readouterr().err


@pytest.mark.parametrize("count", [4, 9])
def test_tags_outside_five_to_eight_are_refused(tmp_path, capsys, count):
    video(tmp_path, meta=metadata(tags=[f"tag {i}" for i in range(count)]))
    assert run(tmp_path) == 3
    assert f"tags: {count}, need 5 to 8" in capsys.readouterr().err


@pytest.mark.parametrize("count", [5, 8])
def test_five_to_eight_tags_pass(tmp_path, count):
    folder = video(tmp_path, meta=metadata(tags=[f"tag {i}" for i in range(count)]))
    assert run(tmp_path) == 0
    assert len(packaged(folder)["tags"]) == count


def test_more_than_three_hashtags_are_refused(tmp_path, capsys):
    video(tmp_path, meta=metadata(hashtags=["#a", "#b", "#c", "#d"]))
    assert run(tmp_path) == 3
    assert "hashtags: 4, at most 3" in capsys.readouterr().err


@pytest.mark.parametrize("tag", ["software testing", "#two words", "#"])
def test_a_hashtag_that_is_not_one_word_is_refused(tmp_path, capsys, tag):
    video(tmp_path, meta=metadata(hashtags=["#ai", tag]))
    assert run(tmp_path) == 3
    assert f"hashtag {tag!r}" in capsys.readouterr().err


def test_angle_brackets_are_refused_since_youtube_rejects_them(tmp_path, capsys):
    video(tmp_path, meta=metadata(hook="Tests <that> pass"))
    assert run(tmp_path) == 3
    assert "angle brackets" in capsys.readouterr().err


def test_a_description_over_five_thousand_characters_is_refused(tmp_path, capsys):
    video(tmp_path, meta=metadata(hook="Words " * 900))
    assert run(tmp_path) == 3
    assert "description: over 5000 characters" in capsys.readouterr().err


def test_paid_promotion_is_disclosed_with_its_sponsor(tmp_path):
    folder = video(tmp_path, meta=metadata(paid_promotion="Example Tools sponsors this video"))
    assert run(tmp_path) == 0
    text = (folder / "description.md").read_text()
    assert "Narration uses a synthetic AI voice.\nIncludes paid promotion: Example Tools sponsors this video.\n" in text
    assert "No paid promotion." not in text
    assert packaged(folder)["paid_promotion"] is True


def test_a_missing_demo_link_is_refused(tmp_path, capsys):
    video(tmp_path, demo=False)
    assert run(tmp_path) == 3
    assert "demo.json" in capsys.readouterr().err


@pytest.mark.parametrize("claims", [None, [claim(1), claim(2, found=False)]])
def test_missing_or_unverified_citations_are_refused(tmp_path, capsys, claims):
    video(tmp_path, citations=claims)
    assert run(tmp_path) == 3
    assert "citations" in capsys.readouterr().err


def test_every_problem_is_named_at_once(tmp_path, capsys):
    video(tmp_path, meta=metadata(title="x" * 99, tags=["one"], chapters=CHAPTERS[:2]), demo=False)
    assert run(tmp_path) == 3
    err = capsys.readouterr().err
    for text in ["title:", "tags:", "chapters:", "demo.json"]:
        assert text in err, text


@pytest.mark.parametrize("field", ["hook", "tags", "paid_promotion"])
def test_a_metadata_file_missing_a_field_is_bad_input(tmp_path, capsys, field):
    meta = metadata()
    del meta[field]
    video(tmp_path, meta=meta)
    assert run(tmp_path) == 2
    assert field in capsys.readouterr().err


def test_a_short_links_its_related_long_form_and_has_no_chapters(tmp_path):
    folder = short(tmp_path)
    assert run(tmp_path, SHORT) == 0
    text = (folder / "description.md").read_text()
    assert text.startswith(f"Two AI-written unit tests pass, and neither can fail.\n\nFull video: {LONG_URL}\n\nCode: ")
    assert "00:00" not in text
    assert packaged(folder)["related_video"] == LONG_URL


def test_a_short_with_chapters_is_refused(tmp_path, capsys):
    short(tmp_path, chapters=CHAPTERS[:3])
    assert run(tmp_path, SHORT) == 3
    assert "a Short has no chapters" in capsys.readouterr().err


def test_a_short_whose_long_form_is_not_published_is_refused(tmp_path, capsys):
    short(tmp_path, related_url=None)
    assert run(tmp_path, SHORT) == 3
    assert "--video-url" in capsys.readouterr().err


def test_a_short_without_its_related_long_form_is_bad_input(tmp_path, capsys):
    folder = short(tmp_path)
    meta = json.loads((folder / "metadata.json").read_text())
    del meta["related"]
    (folder / "metadata.json").write_text(json.dumps(meta))
    assert run(tmp_path, SHORT) == 2
    assert "related" in capsys.readouterr().err


def published(root):
    """A packaged long-form whose demo folder was scaffolded in the clone; its README path."""
    folder = video(root)
    readme = clone(root) / "14-mocked-tests" / "README.md"
    assert (
        scaffold.main(["example", "14", "--slug", "mocked-tests", "--proves", "It passes."], root=root, gh=FakeGitHub())
        == 0
    )
    assert run(root) == 0
    return folder, readme


def test_the_published_url_fills_the_demo_readme_and_the_packaging(tmp_path):
    folder, readme = published(tmp_path)
    assert run(tmp_path, LONG, "--video-url", LONG_URL) == 0
    lines = readme.read_text().splitlines()
    assert f"- Video: {LONG_URL}" in lines and scaffold.VIDEO_PENDING not in lines
    assert f"- Channel: [{CONFIG['name']}]({CONFIG['url']})" in lines
    assert packaged(folder)["video_url"] == LONG_URL


def test_the_readme_sources_are_rebuilt_from_the_final_citations(tmp_path):
    folder, readme = published(tmp_path)
    final = [claim(1), claim(3)]
    (folder / "citations.json").write_text(json.dumps(final))
    assert run(tmp_path, LONG, "--video-url", LONG_URL) == 0
    text = readme.read_text()
    assert final[1]["link"] in text and CITATIONS[1]["link"] not in text
    assert text.rstrip().endswith("MIT; see `LICENSE` at the repository root.")


@pytest.mark.parametrize("url", [SHORT_URL, "https://youtu.be/dQw4w9WgXcQ"])
def test_each_youtube_url_form_is_accepted(tmp_path, url):
    published(tmp_path)
    assert run(tmp_path, LONG, "--video-url", url) == 0


@pytest.mark.parametrize(
    "url", ["https://example.com/watch?v=dQw4w9WgXcQ", "http://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"]
)
def test_a_url_that_is_not_a_youtube_video_is_bad_input(tmp_path, url):
    _, readme = published(tmp_path)
    assert run(tmp_path, LONG, "--video-url", url) == 2
    assert scaffold.VIDEO_PENDING in readme.read_text().splitlines()


def test_packaging_again_keeps_the_recorded_video_url(tmp_path):
    folder, _ = published(tmp_path)
    assert run(tmp_path, LONG, "--video-url", LONG_URL) == 0
    assert run(tmp_path) == 0
    assert packaged(folder)["video_url"] == LONG_URL


def test_a_short_cut_from_the_long_form_leaves_the_long_form_readme(tmp_path):
    _, readme = published(tmp_path)
    assert run(tmp_path, LONG, "--video-url", LONG_URL) == 0
    meta = metadata(chapters=[], related=LONG)
    folder = video(tmp_path, SHORT, "short", meta, seconds=[10, 15, 20])
    assert run(tmp_path, SHORT) == 0
    assert run(tmp_path, SHORT, "--video-url", SHORT_URL) == 0
    assert f"- Video: {LONG_URL}" in readme.read_text().splitlines()
    assert packaged(folder)["video_url"] == SHORT_URL


def test_the_video_url_before_packaging_is_refused(tmp_path, capsys):
    video(tmp_path)
    assert run(tmp_path, LONG, "--video-url", LONG_URL) == 3
    assert "package" in capsys.readouterr().err
