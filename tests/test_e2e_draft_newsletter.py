"""End-to-end test of the draft-newsletter CLI against a fixture video folder.

The test keeps the real config loader, Markdown converter, Jinja2 template, Kit
client, and CLI wiring. Only the two external I/O boundaries are faked: Kit's
HTTP transport and the GitHub issue client.
"""

import importlib.util
import json
import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import httpx
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "agentic" / "skills" / "content" / "draft-newsletter"
SCRIPTS = SKILL / "scripts"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_github_module = _load("github_client", SCRIPTS / "github_client.py")
_draft = _load("draft_newsletter", SCRIPTS / "draft_newsletter.py")

GitHubIssueClient = _github_module.GitHubIssueClient

VIDEO_ISSUE = 123
VIDEO_PROJECT = "e2e-video-project"
NEWSLETTER_PROJECT = "e2e-newsletter"


@pytest.fixture
def workspace(tmp_path):
    """Fixture video folder plus a newsletter project config in a temp repo root."""
    video = tmp_path / ".projects" / "youtube" / VIDEO_PROJECT / "videos" / str(VIDEO_ISSUE)
    video.mkdir(parents=True)
    fixture = ROOT / "tests" / "fixtures" / "videos" / "123"
    (video / "script.md").write_text((fixture / "script.md").read_text())
    (video / "citations.md").write_text((fixture / "citations.md").read_text())

    config_dir = tmp_path / ".projects" / "content" / NEWSLETTER_PROJECT
    config_dir.mkdir(parents=True)
    config_path = config_dir / "config.yaml"
    config_path.write_text(
        yaml.dump(
            {
                "platform": "kit",
                "publication_id": "test-pub-123",
                "sender_name": "OneO4 Team",
                "sender_email": "newsletter@example.com",
                "signup_url": "https://old.example.com/subscribe",
            },
            sort_keys=False,
        )
    )

    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    yield {
        "root": tmp_path,
        "video": video,
        "config": config_path,
    }
    os.chdir(old_cwd)


def _kit_recorder(record: list) -> httpx.MockTransport:
    """Fake Kit HTTP responses and record the requests the client sends."""

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content) if request.content else {}
        if request.url.path.endswith("/drafts"):
            record.append(("draft", body))
            return httpx.Response(
                200,
                json={
                    "id": 4242,
                    "preview_url": "https://app.kit.com/publishers/test-pub-123/drafts/4242",
                },
            )
        if request.url.path.endswith("/send"):
            record.append(("send", body))
            return httpx.Response(200, json={"status": "ok"})
        return httpx.Response(404)

    return httpx.MockTransport(handler)


def _github_client(approved: bool) -> Mock:
    client = Mock(spec=GitHubIssueClient)
    client.has_label.return_value = approved
    client.has_approval_comment.return_value = False
    client.latest_comment_time.return_value = datetime.now(UTC) - timedelta(minutes=1)
    client.__enter__ = Mock(return_value=client)
    client.__exit__ = Mock(return_value=False)
    return client


def _run_with_fakes(record: list, github: Mock, **kwargs):
    """Run the CLI against a real Kit client over a fake HTTP transport."""
    transport = _kit_recorder(record)
    real_client = httpx.Client

    def factory(*args, **client_kwargs):
        client_kwargs["transport"] = transport
        return real_client(*args, **client_kwargs)

    with (
        patch.object(httpx, "Client", side_effect=factory),
        patch.object(_draft, "GitHubIssueClient", return_value=github),
    ):
        return _draft.run(VIDEO_ISSUE, VIDEO_PROJECT, NEWSLETTER_PROJECT, **kwargs)


@patch.dict(
    os.environ,
    {
        "KIT_API_KEY": "test-api-key",
        "GH_TOKEN": "test-token",
        "GITHUB_REPOSITORY": "owner/repo",
    },
)
def test_end_to_end_approved(workspace):
    """One published fixture video reaches a sent Kit draft end to end."""
    record = []
    github = _github_client(approved=True)

    result = _run_with_fakes(record, github)

    # AC2: newsletter.md came from the fixture and the HTML kept its code block.
    newsletter_md = workspace["video"] / "newsletter.md"
    assert newsletter_md.exists()
    rendered = newsletter_md.read_text()
    assert "Building a CLI Tool in Python" in rendered
    assert "https://youtube.com/watch?v=test123" in rendered
    assert "Use argparse for standard library CLI parsing" in rendered

    kind, draft = record[0]
    assert kind == "draft"
    assert "language-python" in draft["html"]
    assert "argparse" in draft["html"]
    assert draft["subject"] == "Newsletter: Test Video: Building a CLI Tool in Python"

    # AC3: draft id and preview URL come back.
    assert result["draft_id"] == "4242"
    assert result["preview_url"] == "https://app.kit.com/publishers/test-pub-123/drafts/4242"

    # AC4 and AC8: the owner's yes was recorded and the labels ran in order.
    assert record[1][0] == "send"
    labels = [call.args[1] for call in github.add_label.call_args_list]
    assert labels == ["newsletter:draft", "newsletter:approved", "newsletter:sent"]
    assert result["sent"] is True

    # AC7: the Kit signup URL replaced the old value in the config file.
    saved = yaml.safe_load(workspace["config"].read_text())
    assert saved["signup_url"] == "https://test-pub-123.kit.com/subscribe"
    assert saved["publication_id"] == "test-pub-123"


@patch.dict(
    os.environ,
    {
        "KIT_API_KEY": "test-api-key",
        "GH_TOKEN": "test-token",
        "GITHUB_REPOSITORY": "owner/repo",
    },
)
def test_end_to_end_without_owner_yes_sends_nothing(workspace):
    """With no owner yes, the draft stays a draft and the run times out."""
    record = []
    github = _github_client(approved=False)

    result = _run_with_fakes(
        record,
        github,
        approval_poll_interval=0.01,
        approval_timeout=0.05,
    )

    assert [kind for kind, _ in record] == ["draft"]
    labels = [call.args[1] for call in github.add_label.call_args_list]
    assert labels == ["newsletter:draft", "newsletter:timeout"]
    assert result["sent"] is False
