"""Tests for the scan-video-ideas skill's scripts/competition.py, with a fake YouTube API."""

import datetime
import io
import json
import sys
import urllib.error
from pathlib import Path

import pytest
import yaml
import youtube_channel as yc

# A script serving one skill stays in the skill (components.md), outside the pytest pythonpath.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agentic/skills/content/scan-video-ideas/scripts"))
import competition

TODAY = datetime.date(2026, 10, 23)
KEY = "fake-key-not-real"

CHANNEL = {
    "name": "Example Lab",
    "url": "https://example.com/channel/example-lab",
    "voice": {"id": "Puck", "style": "warm", "pace": 0.92},
    "palette": {"background": "#000000", "syntax": "#FF3B3B", "name": "#FFFFFF", "suffix": "#00E5FF"},
    "loudness": {"lufs": -14, "true_peak": -1.0},
    "music_db": -24,
    "cadence": {"long_form_per_week": 1, "shorts_per_week": 2, "owner_hours_per_week": 5},
    "labels": {"channel": "channel:example-lab"},
    "pronunciation": {},
    "banned_phrases": [],
    "title_max": 60,
    "demos": {"repo": "example-org/example-demos", "path": "example-demos"},
    "thumbnail": {"art_style": "3D clay render"},
    "branding": {"wordmarks": ["testlab"], "tagline": "How testers think", "subline": "weekly"},
}

SCORES = {"lens": 5, "proof": 5, "freshness": 5, "audience_pull": 5, "distinctness": 5, "effort": 5}

CARD = {
    "title": "Your AI Wrote Checks, Not Tests",
    "pillar": "Testing AI",
    "rst_concept": "Testing vs checking",
    "claim": "AI writes great unit tests",
    "tester_question": "Can any of these tests fail for a reason that matters?",
    "proof": "Mutation run on AI-written tests",
    "format": "long-form",
    "hook": "evergreen",
    "sources": ["https://example.com/testing-vs-checking"],
    "risks": ["accuracy of mutation numbers"],
    "scores": SCORES,
    "query": "AI generated unit tests mutation testing",
    "anchors": [["unit test"], ["ai", "llm"]],
}

TOPICAL = {
    "id": "topical1",
    "snippet": {
        "title": "Are AI unit tests any good?",
        "description": "We run mutation testing on LLM output.",
        "channelTitle": "Some Channel",
        "publishedAt": "2026-10-13T10:00:00Z",
    },
    "statistics": {"viewCount": "1000"},
    "contentDetails": {"duration": "PT8M30S"},
}
OFF_TOPIC = {
    "id": "offtopic1",
    "snippet": {
        "title": "Unit test maintainability in Java",
        "description": "x" * 400 + " written with AI",  # the anchor is past the description start
        "channelTitle": "Other Channel",
        "publishedAt": "2026-01-01T00:00:00Z",
    },
    "statistics": {"viewCount": "50000"},
    "contentDetails": {"duration": "PT1H2M"},
}


class FakeYouTube:
    """Answers search and videos calls and records each one."""

    def __init__(self, items=(TOPICAL, OFF_TOPIC)):
        self.items = list(items)
        self.calls: list[tuple[str, dict]] = []

    def __call__(self, endpoint, params):
        self.calls.append((endpoint, params))
        if endpoint == "search":
            return {"items": [{"id": {"videoId": item["id"]}} for item in self.items]}
        return {"items": self.items}

    def count(self, endpoint):
        return sum(1 for name, _ in self.calls if name == endpoint)


@pytest.fixture
def root(tmp_path, monkeypatch):
    monkeypatch.setenv(competition.KEY_VARIABLE, KEY)
    path = tmp_path / ".projects" / "content" / "yt-example"
    path.mkdir(parents=True)
    (path / "channel.yaml").write_text(yaml.safe_dump(CHANNEL))
    (path / "style-guide.md").write_text("".join(f"## {s}\n\nRules.\n\n" for s in yc.SECTIONS))
    return tmp_path


def write_card(root, card=CARD, name="card.json"):
    path = root / name
    path.write_text(json.dumps(card))
    return path


def run(root, card_path, http, today=TODAY, extra=()):
    return competition.main(["example", str(card_path), *extra], http=http, root=root, today=today)


def output(capsys):
    return json.loads(capsys.readouterr().out)


@pytest.mark.parametrize("field", competition.REQUIRED)
def test_card_missing_a_required_field_is_refused_naming_it(root, capsys, field):
    card = {k: v for k, v in CARD.items() if k != field}
    fake = FakeYouTube()
    assert run(root, write_card(root, card), fake) == 2
    assert field in capsys.readouterr().err
    assert fake.calls == []


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("pillar", "  "),
        ("format", "series"),
        ("sources", []),
        ("sources", ["not a link"]),
        ("risks", []),
        ("anchors", [[]]),
        ("scores", {**SCORES, "lens": 6}),
        ("scores", {k: v for k, v in SCORES.items() if k != "effort"}),
    ],
)
def test_card_with_an_invalid_field_is_refused_naming_it(root, capsys, field, value):
    assert run(root, write_card(root, {**CARD, field: value}), FakeYouTube()) == 2
    assert field in capsys.readouterr().err


@pytest.mark.parametrize(
    ("scores", "total", "parked"),
    [
        (SCORES, 65, False),
        ({k: 1 for k in SCORES}, 13, True),
        ({"lens": 5, "proof": 4, "freshness": 3, "audience_pull": 2, "distinctness": 1, "effort": 5}, 44, False),
        ({k: 3 for k in SCORES}, 39, True),
        ({**{k: 3 for k in SCORES}, "effort": 4}, 40, False),
    ],
)
def test_score_weights_each_factor_out_of_65_and_parks_under_40(root, capsys, scores, total, parked):
    assert run(root, write_card(root, {**CARD, "scores": scores}), FakeYouTube()) == 0
    score = output(capsys)["score"]
    assert (score["total"], score["max"], score["parked"]) == (total, 65, parked)


def test_relevance_filter_keeps_topical_videos_and_drops_off_topic_ones(root, capsys):
    assert run(root, write_card(root), FakeYouTube()) == 0
    videos = output(capsys)["videos"]
    assert [v["url"] for v in videos] == ["https://www.youtube.com/watch?v=topical1"]
    assert videos[0] == {
        "title": "Are AI unit tests any good?",
        "channel": "Some Channel",
        "url": "https://www.youtube.com/watch?v=topical1",
        "published": "2026-10-13",
        "views": 1000,
        "views_per_day": 100.0,
        "minutes": 8.5,
    }


def test_search_asks_for_videos_and_passes_the_key(root, capsys):
    fake = FakeYouTube()
    run(root, write_card(root), fake)
    endpoint, params = fake.calls[0]
    assert (endpoint, params["type"], params["q"], params["key"]) == ("search", "video", CARD["query"], KEY)
    assert fake.calls[1][0] == "videos"
    assert fake.calls[1][1]["id"] == "topical1,offtopic1"


def test_cached_query_is_not_searched_again_the_same_day(root, capsys):
    fake = FakeYouTube()
    card = write_card(root)
    assert run(root, card, fake) == 0
    first = output(capsys)
    assert run(root, card, fake) == 0
    assert (fake.count("search"), fake.count("videos")) == (1, 1)
    assert output(capsys)["videos"] == first["videos"]
    assert list((root / ".projects/content/yt-example/research/competition-cache").iterdir())


def test_cached_query_needs_no_key(root, capsys, monkeypatch):
    card = write_card(root)
    run(root, card, FakeYouTube())
    monkeypatch.delenv(competition.KEY_VARIABLE)
    fake = FakeYouTube()
    assert run(root, card, fake) == 0
    assert fake.calls == []


def test_cached_query_is_searched_again_the_next_day(root, capsys):
    fake = FakeYouTube()
    card = write_card(root)
    run(root, card, fake)
    run(root, card, fake, today=TODAY + datetime.timedelta(days=1))
    assert fake.count("search") == 2


def test_another_query_is_searched_on_its_own(root, capsys):
    fake = FakeYouTube()
    run(root, write_card(root), fake)
    run(root, write_card(root, {**CARD, "query": "test oracle"}, "other.json"), fake)
    assert fake.count("search") == 2


def test_queries_sharing_a_slug_keep_their_own_cache(root, capsys):
    fake = FakeYouTube()
    first = write_card(root, {**CARD, "query": "AI unit tests: mutation"}, "a.json")
    second = write_card(root, {**CARD, "query": "ai unit tests mutation"}, "b.json")
    for card in (first, second, first):
        assert run(root, card, fake) == 0
    assert fake.count("search") == 2
    assert len(list((root / ".projects/content/yt-example/research/competition-cache").iterdir())) == 2


def test_missing_key_is_refused_without_calling_youtube(root, capsys, monkeypatch):
    monkeypatch.delenv(competition.KEY_VARIABLE)
    fake = FakeYouTube()
    assert run(root, write_card(root), fake) == 2
    assert competition.KEY_VARIABLE in capsys.readouterr().err
    assert fake.calls == []


def test_api_error_exits_1_without_printing_the_key(root, capsys, monkeypatch):
    def refuse(request, timeout):
        body = io.BytesIO(b'{"error": {"message": "quota exceeded"}}')
        raise urllib.error.HTTPError(request.full_url, 403, "Forbidden", {}, body)

    monkeypatch.setattr(competition.urllib.request, "urlopen", refuse)
    assert run(root, write_card(root), competition.fetch) == 1
    captured = capsys.readouterr()
    assert "403" in captured.err and "quota exceeded" in captured.err
    assert KEY not in captured.out + captured.err


def test_markdown_card_is_written_next_to_the_card(root, capsys):
    card = write_card(root)
    assert run(root, card, FakeYouTube()) == 0
    text = card.with_suffix(".md").read_text()
    assert CARD["tester_question"] in text
    assert "65 / 65" in text
    assert "https://www.youtube.com/watch?v=topical1" in text
    assert "offtopic1" not in text


def test_invalid_channel_is_refused(root, capsys):
    assert competition.main(["nochannel", str(write_card(root))], http=FakeYouTube(), root=root, today=TODAY) == 2
