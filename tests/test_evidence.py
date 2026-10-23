"""Tests for the research-video skill's scripts/evidence.py, with a fake page fetcher."""

import datetime
import json
import sys
from pathlib import Path

import pytest
from test_youtube_channel import workspace

# A script serving one skill stays in the skill (components.md), outside the pytest pythonpath.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agentic/skills/content/research-video/scripts"))
import evidence

DOCS = "https://playwright.dev/docs/test-agents"


@pytest.mark.parametrize(
    ("url", "quote", "link"),
    [
        (
            DOCS,
            "Re-runs the test until it passes or until guardrails stop the loop",
            DOCS + "#:~:text=Re%2Druns%20the%20test%20until,stop%20the%20loop",
        ),
        (DOCS, "planner, generator and healer", DOCS + "#:~:text=planner%2C%20generator%20and%20healer"),
        (DOCS + "#agents", "A & B", DOCS + "#agents:~:text=A%20%26%20B"),
    ],
)
def test_link_opens_the_page_at_the_quote_with_a_text_fragment(url, quote, link):
    assert evidence.fragment_link(url, quote) == link


# Checking claims through main, with a fake fetcher and a fixed clock

NOW = datetime.datetime(2026, 10, 23, 9, 30, tzinfo=datetime.UTC)
SATISFICE = "https://www.satisfice.com/blog/archives/856"
PAGES = {
    DOCS: "Healer\n  Re-runs the test until it passes\n or until guardrails stop the loop.",
    SATISFICE: "Checking is the mechanistic process of verifying propositions about the product.",
}
CLAIMS = [
    {
        "id": "C1",
        "claim": "The healer reruns a test until it passes.",
        "url": DOCS,
        "quote": "Re-runs the test until it passes or until guardrails stop the loop",
    },
    {
        "id": "C2",
        "claim": "A check verifies propositions.",
        "url": SATISFICE,
        "quote": "Checking is the mechanistic process of verifying propositions about the product",
    },
]


class FakeFetcher:
    """Answers each url from pages, and records each call's urls."""

    def __init__(self, pages=PAGES):
        self.pages = pages
        self.calls = []

    def __call__(self, urls):
        self.calls.append(list(urls))
        return {url: self.pages[url] for url in urls}


def citations_file(root, claims=CLAIMS, number=12):
    path = workspace(root) / "videos" / str(number) / "citations.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(claims, indent=1))
    return path


def check(root, fetcher, number=12):
    return evidence.main(["example", str(number)], fetch=fetcher, root=root, now=lambda: NOW)


def test_check_marks_each_quote_found_on_its_live_page_with_its_link(tmp_path):
    path = citations_file(tmp_path)
    assert check(tmp_path, FakeFetcher()) == 0
    claims = json.loads(path.read_text())
    assert [c["found"] for c in claims] == [True, True]
    assert {c["checked"] for c in claims} == {"2026-10-23T09:30:00+00:00"}
    assert claims[0]["link"] == evidence.fragment_link(DOCS, CLAIMS[0]["quote"])
    assert claims[0]["quote"] == CLAIMS[0]["quote"]


def test_check_refuses_a_quote_missing_from_its_page_and_names_the_claim(tmp_path, capsys):
    path = citations_file(tmp_path)
    pages = PAGES | {SATISFICE: "Checking is part of testing."}
    assert check(tmp_path, FakeFetcher(pages)) == 3
    assert [c["found"] for c in json.loads(path.read_text())] == [True, False]
    err = capsys.readouterr().err
    assert "C2" in err and SATISFICE in err
    assert "C1" not in err


@pytest.mark.parametrize(
    ("quote", "page", "found"),
    [
        ("verifying  propositions\nabout the product", "of verifying propositions about the product.", True),
        ("verifying propositions about the product", "of verifying propositions\n\tabout the\r\nproduct", True),
        ("Verifying propositions", "of verifying propositions", False),
        ("verifying propositions, about", "of verifying propositions about", False),
    ],
)
def test_check_matches_the_exact_quote_with_only_whitespace_normalised(tmp_path, quote, page, found):
    path = citations_file(tmp_path, [CLAIMS[1] | {"quote": quote}])
    assert check(tmp_path, FakeFetcher({SATISFICE: page})) == (0 if found else 3)
    assert json.loads(path.read_text())[0]["found"] is found


@pytest.mark.parametrize(
    ("claims", "problem"),
    [
        ([], "citations.json: must be a non-empty list of claims"),
        ({"C1": CLAIMS[0]}, "citations.json: must be a non-empty list of claims"),
        (["C1"], "claim 1: must be a JSON object"),
        ([{k: v for k, v in CLAIMS[0].items() if k != "quote"}], "C1: quote: missing"),
        ([CLAIMS[0] | {"quote": "  "}], "C1: quote: must be a non-empty string"),
        ([CLAIMS[0] | {"claim": 7}], "C1: claim: must be a non-empty string"),
        ([CLAIMS[0] | {"url": "http://playwright.dev"}], "C1: url: must be an https:// link"),
        ([CLAIMS[0] | {"id": "one"}], "claim 1: id: must be C followed by a number, such as C1"),
        ([CLAIMS[0], CLAIMS[1] | {"id": "C1"}], "C1: id: used by more than one claim"),
    ],
)
def test_check_rejects_an_invalid_citations_file_without_fetching(tmp_path, capsys, claims, problem):
    path = citations_file(tmp_path, claims)
    before = path.read_text()
    fetcher = FakeFetcher()
    assert check(tmp_path, fetcher) == 2
    assert problem in capsys.readouterr().err
    assert fetcher.calls == []
    assert path.read_text() == before


@pytest.mark.parametrize("text", [None, "{not json"])
def test_check_rejects_a_missing_or_unreadable_citations_file(tmp_path, capsys, text):
    folder = workspace(tmp_path) / "videos" / "12"
    folder.mkdir(parents=True)
    if text is not None:
        (folder / "citations.json").write_text(text)
    assert check(tmp_path, FakeFetcher()) == 2
    assert "citations.json" in capsys.readouterr().err


def test_check_rejects_an_invalid_channel(tmp_path, capsys):
    workspace(tmp_path, guide=False)
    assert check(tmp_path, FakeFetcher()) == 2
    assert "style-guide.md" in capsys.readouterr().err


def test_check_loads_each_source_page_once(tmp_path):
    citations_file(tmp_path, [*CLAIMS, CLAIMS[0] | {"id": "C3", "quote": "Healer"}])
    fetcher = FakeFetcher()
    assert check(tmp_path, fetcher) == 0
    assert fetcher.calls == [[DOCS, SATISFICE]]


def test_check_records_a_page_that_failed_to_load_as_not_found(tmp_path, capsys):
    path = citations_file(tmp_path)
    pages = PAGES | {SATISFICE: evidence.PageError("HTTP 404")}
    assert check(tmp_path, FakeFetcher(pages)) == 1
    claims = json.loads(path.read_text())
    assert [c["found"] for c in claims] == [True, False]
    assert claims[1]["error"] == "HTTP 404"
    assert f"C2: {SATISFICE}: HTTP 404" in capsys.readouterr().err
    assert check(tmp_path, FakeFetcher()) == 0
    assert "error" not in json.loads(path.read_text())[1]
