"""Integration tests for the draft_newsletter CLI entry point."""

import importlib.util
import json
import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
SKILL_SCRIPTS = ROOT / "agentic" / "skills" / "content" / "draft-newsletter" / "scripts"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_kit_module = _load("kit_client", SKILL_SCRIPTS / "kit_client.py")
_github_module = _load("github_client", SKILL_SCRIPTS / "github_client.py")
_draft_newsletter_module = _load("draft_newsletter", SKILL_SCRIPTS / "draft_newsletter.py")

main = _draft_newsletter_module.main
run = _draft_newsletter_module.run
read_script_and_citations = _draft_newsletter_module.read_script_and_citations
extract_metadata = _draft_newsletter_module.extract_metadata
render_newsletter = _draft_newsletter_module.render_newsletter
write_newsletter_md = _draft_newsletter_module.write_newsletter_md
wait_for_approval_label = _draft_newsletter_module.wait_for_approval_label
_exit_code = _draft_newsletter_module._exit_code

KitClient = _kit_module.KitClient
DraftResponse = _kit_module.DraftResponse
GitHubIssueClient = _github_module.GitHubIssueClient

VIDEO_PROJECT = "test-video-project"
NEWSLETTER_PROJECT = "test-newsletter"
VIDEO_ISSUE = 42


class TestDraftNewsletterIntegration:
    """Integration tests for the draft_newsletter main flow."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create a temporary project structure with config and video folder."""
        config_dir = tmp_path / ".projects" / "content" / NEWSLETTER_PROJECT
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config.yaml"
        config_file.write_text(
            yaml.dump(
                {
                    "platform": "kit",
                    "publication_id": "test-pub-123",
                    "sender_name": "Test Sender",
                    "sender_email": "test@example.com",
                    "signup_url": "https://old-signup.com/subscribe",
                },
                sort_keys=False,
            )
        )

        video_folder = tmp_path / ".projects" / "youtube" / VIDEO_PROJECT / "videos" / str(VIDEO_ISSUE)
        video_folder.mkdir(parents=True)
        (video_folder / "script.md").write_text(
            """# Test Video Title

**Video URL:** https://youtube.com/watch?v=test123

## Summary

This video shows how to build a CLI tool in Python.

## Key Points

- Use argparse for parsing
- Add helpful exit codes
- Write tests first
"""
        )
        (video_folder / "citations.md").write_text(
            """# Citations

## References

1. [Python Documentation](https://docs.python.org/3/)

```python
def hello():
    print("Hello, World!")
```
"""
        )

        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        yield {
            "config_file": config_file,
            "video_folder": video_folder,
            "tmp_path": tmp_path,
        }
        os.chdir(old_cwd)

    @pytest.fixture
    def mock_kit_client(self):
        """Create a mocked KitClient with a recorded draft response."""
        with patch.object(KitClient, "__init__", lambda self, api_key, publication_id: None):
            client = KitClient.__new__(KitClient)
            client.api_key = "test-api-key"
            client.publication_id = "test-pub-123"
            client._client = Mock()
            yield client

    @pytest.fixture
    def mock_github_client(self):
        """Create a mocked GitHubIssueClient."""
        with patch.object(GitHubIssueClient, "__init__", lambda self, repo, token: None):
            client = GitHubIssueClient.__new__(GitHubIssueClient)
            client.repo = "owner/repo"
            client.token = "test-token"
            client.remove_label = Mock()
            yield client

    def test_read_script_and_citations(self, temp_project):
        """Test reading script.md and citations.md from video folder."""
        script, citations = read_script_and_citations(VIDEO_PROJECT, VIDEO_ISSUE)
        assert "Test Video Title" in script
        assert "References" in citations

    def test_read_script_and_citations_missing_files(self, temp_project):
        """Test missing files raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="script.md not found"):
            read_script_and_citations(VIDEO_PROJECT, 999)

    def test_extract_metadata(self, temp_project):
        """Test metadata extraction from the script."""
        script, citations = read_script_and_citations(VIDEO_PROJECT, VIDEO_ISSUE)
        metadata = extract_metadata(script, citations, VIDEO_ISSUE, signup_url="https://x/signup")

        assert metadata["video_title"] == "Test Video Title"
        assert metadata["video_url"] == "https://youtube.com/watch?v=test123"
        assert metadata["script_summary"] == "This video shows how to build a CLI tool in Python."
        assert metadata["key_points"] == [
            "Use argparse for parsing",
            "Add helpful exit codes",
            "Write tests first",
        ]
        assert metadata["signup_url"] == "https://x/signup"

    def test_extract_metadata_from_fixture(self):
        """Test metadata extraction on the committed video fixture."""
        fixture = ROOT / "tests" / "fixtures" / "videos" / "123"
        script = (fixture / "script.md").read_text()
        citations = (fixture / "citations.md").read_text()

        metadata = extract_metadata(script, citations, 123)

        assert metadata["video_title"] == "Test Video: Building a CLI Tool in Python"
        assert metadata["video_url"] == "https://youtube.com/watch?v=test123"
        assert metadata["script_summary"].startswith("This video demonstrates")
        assert "Use argparse for standard library CLI parsing" in metadata["key_points"]
        assert metadata["script_summary"] != "**Video URL:** https://youtube.com/watch?v=test123"

    def test_extract_metadata_requires_title(self):
        """A script without a title heading is an error, not an invented title."""
        with pytest.raises(ValueError, match="has no title heading"):
            extract_metadata("**Video URL:** https://example.com\n", "", 123)

    def test_extract_metadata_requires_video_url(self):
        """A script without a Video URL line is an error, not an invented URL."""
        with pytest.raises(ValueError, match="Video URL"):
            extract_metadata("# Title\n\n## Summary\nText\n", "", 123)

    def test_render_newsletter(self, temp_project):
        """Test newsletter rendering, including the Kit unsubscribe merge tag."""
        script, citations = read_script_and_citations(VIDEO_PROJECT, VIDEO_ISSUE)
        metadata = extract_metadata(script, citations, VIDEO_ISSUE, signup_url="https://x/signup")

        rendered = render_newsletter(metadata)

        assert "# Test Video Title" in rendered
        assert "https://youtube.com/watch?v=test123" in rendered
        assert "https://x/signup" in rendered
        assert "{{ unsubscribe_url }}" in rendered
        assert "/subscribe/unsubscribe" not in rendered

    def test_write_newsletter_md(self, temp_project):
        """Test newsletter.md is written to the video folder."""
        output = write_newsletter_md("# Newsletter", VIDEO_PROJECT, VIDEO_ISSUE)

        assert output.exists()
        assert output.name == "newsletter.md"
        assert output.read_text() == "# Newsletter"

    @patch.dict(
        os.environ,
        {"KIT_API_KEY": "test-api-key", "GH_TOKEN": "test-token", "GITHUB_REPOSITORY": "owner/repo"},
    )
    def test_main_flow_approved(self, temp_project, mock_kit_client, mock_github_client):
        """Test the full flow: draft, approve, send, and every side effect."""
        draft = DraftResponse(
            preview_url="https://app.kit.com/publishers/test-pub-123/drafts/draft-456",
            draft_id="draft-456",
        )
        mock_kit_client.create_draft = Mock(return_value=draft)
        mock_kit_client.send_draft = Mock(return_value=Mock(success=True, message="Sent"))
        mock_kit_client.get_signup_url = Mock(return_value="https://test-pub-123.kit.com/subscribe")
        mock_kit_client.update_signup_url_in_config = Mock()

        mock_github_client.add_label = Mock()
        mock_github_client.add_comment = Mock()
        mock_github_client.latest_comment_time = Mock(return_value=None)

        with (
            patch.object(_draft_newsletter_module, "wait_for_approval_label", return_value=True),
            patch.object(_draft_newsletter_module, "KitClient", return_value=mock_kit_client),
            patch.object(_draft_newsletter_module, "GitHubIssueClient", return_value=mock_github_client),
            patch.object(_draft_newsletter_module, "get_kit_api_key", return_value="test-api-key"),
        ):
            result = run(VIDEO_ISSUE, VIDEO_PROJECT, NEWSLETTER_PROJECT)

        assert result["draft_id"] == "draft-456"
        assert result["preview_url"] == draft.preview_url
        assert result["sent"] is True
        assert result["signup_url"] == "https://test-pub-123.kit.com/subscribe"

        # AC2: newsletter.md written to the video folder.
        newsletter_md = temp_project["video_folder"] / "newsletter.md"
        assert newsletter_md.exists()
        assert "Test Video Title" in newsletter_md.read_text()

        # AC3: the draft is created from converted HTML for the right subject.
        html, subject = mock_kit_client.create_draft.call_args.args
        assert "<pre" in html and "<code" in html
        assert "language-python" in html
        assert subject == "Newsletter: Test Video Title"

        # AC4: sent only after the approval check.
        mock_kit_client.send_draft.assert_called_once_with("draft-456")

        # AC7: signup URL written to the newsletter project config.
        mock_kit_client.update_signup_url_in_config.assert_called_once_with(NEWSLETTER_PROJECT)

        # AC8: labels in order.
        labels = [call.args[1] for call in mock_github_client.add_label.call_args_list]
        assert labels == ["newsletter:draft", "newsletter:approved", "newsletter:sent"]

    @patch.dict(
        os.environ,
        {"KIT_API_KEY": "test-api-key", "GH_TOKEN": "test-token", "GITHUB_REPOSITORY": "owner/repo"},
    )
    def test_run_clears_stale_approval_label(self, temp_project, mock_kit_client, mock_github_client):
        """run() removes a stale newsletter:approve label before the new draft (AC2)."""
        draft = DraftResponse(
            preview_url="https://app.kit.com/publishers/test-pub-123/drafts/draft-456",
            draft_id="draft-456",
        )
        mock_kit_client.create_draft = Mock(return_value=draft)
        mock_kit_client.send_draft = Mock()
        mock_kit_client.get_signup_url = Mock(return_value="https://test-pub-123.kit.com/subscribe")
        mock_kit_client.update_signup_url_in_config = Mock()

        mock_github_client.has_label = Mock(return_value=True)
        mock_github_client.add_label = Mock()
        mock_github_client.add_comment = Mock()
        mock_github_client.remove_label = Mock()
        mock_github_client.latest_comment_time = Mock(return_value=None)

        with (
            patch.object(_draft_newsletter_module, "wait_for_approval_label", return_value=False),
            patch.object(_draft_newsletter_module, "KitClient", return_value=mock_kit_client),
            patch.object(_draft_newsletter_module, "GitHubIssueClient", return_value=mock_github_client),
            patch.object(_draft_newsletter_module, "get_kit_api_key", return_value="test-api-key"),
        ):
            run(VIDEO_ISSUE, VIDEO_PROJECT, NEWSLETTER_PROJECT)

        # remove_label runs before add_label posts newsletter:draft.
        assert mock_github_client.remove_label.call_args_list[0].args == (
            VIDEO_ISSUE,
            "newsletter:approve",
        )
        assert mock_github_client.add_label.call_args_list[0].args == (
            VIDEO_ISSUE,
            "newsletter:draft",
        )

    @patch.dict(
        os.environ,
        {"KIT_API_KEY": "test-api-key", "GH_TOKEN": "test-token", "GITHUB_REPOSITORY": "owner/repo"},
    )
    def test_run_clears_all_prior_stage_labels(self, temp_project, mock_kit_client, mock_github_client):
        """run() clears every prior stage label before posting newsletter:draft (AC3)."""
        draft = DraftResponse(
            preview_url="https://app.kit.com/publishers/test-pub-123/drafts/draft-456",
            draft_id="draft-456",
        )
        mock_kit_client.create_draft = Mock(return_value=draft)
        mock_kit_client.send_draft = Mock()
        mock_kit_client.get_signup_url = Mock(return_value="https://test-pub-123.kit.com/subscribe")
        mock_kit_client.update_signup_url_in_config = Mock()

        mock_github_client.has_label = Mock(return_value=True)
        mock_github_client.add_label = Mock()
        mock_github_client.add_comment = Mock()
        mock_github_client.remove_label = Mock()
        mock_github_client.latest_comment_time = Mock(return_value=None)

        with (
            patch.object(_draft_newsletter_module, "wait_for_approval_label", return_value=False),
            patch.object(_draft_newsletter_module, "KitClient", return_value=mock_kit_client),
            patch.object(_draft_newsletter_module, "GitHubIssueClient", return_value=mock_github_client),
            patch.object(_draft_newsletter_module, "get_kit_api_key", return_value="test-api-key"),
        ):
            run(VIDEO_ISSUE, VIDEO_PROJECT, NEWSLETTER_PROJECT)

        removed = [call.args[1] for call in mock_github_client.remove_label.call_args_list]
        assert removed == ["newsletter:approve", "newsletter:approved", "newsletter:sent", "newsletter:timeout"]
        assert mock_github_client.add_label.call_args_list[0].args == (VIDEO_ISSUE, "newsletter:draft")

    @patch.dict(
        os.environ,
        {"KIT_API_KEY": "test-api-key", "GH_TOKEN": "test-token", "GITHUB_REPOSITORY": "owner/repo"},
    )
    def test_main_flow_timeout(self, temp_project, mock_kit_client, mock_github_client):
        """Test that nothing is sent when the owner has not approved."""
        draft = DraftResponse(
            preview_url="https://app.kit.com/publishers/test-pub-123/drafts/draft-456",
            draft_id="draft-456",
        )
        mock_kit_client.create_draft = Mock(return_value=draft)
        mock_kit_client.send_draft = Mock()
        mock_kit_client.get_signup_url = Mock(return_value="https://test-pub-123.kit.com/subscribe")
        mock_kit_client.update_signup_url_in_config = Mock()

        mock_github_client.add_label = Mock()
        mock_github_client.add_comment = Mock()
        mock_github_client.latest_comment_time = Mock(return_value=None)

        with (
            patch.object(_draft_newsletter_module, "wait_for_approval_label", return_value=False),
            patch.object(_draft_newsletter_module, "KitClient", return_value=mock_kit_client),
            patch.object(_draft_newsletter_module, "GitHubIssueClient", return_value=mock_github_client),
            patch.object(_draft_newsletter_module, "get_kit_api_key", return_value="test-api-key"),
        ):
            result = run(VIDEO_ISSUE, VIDEO_PROJECT, NEWSLETTER_PROJECT)

        assert result["sent"] is False
        mock_kit_client.send_draft.assert_not_called()

        labels = [call.args[1] for call in mock_github_client.add_label.call_args_list]
        assert labels == ["newsletter:draft", "newsletter:timeout"]
        assert "newsletter:approved" not in labels
        assert "newsletter:sent" not in labels

    @patch.dict(
        os.environ,
        {"KIT_API_KEY": "test-api-key", "GH_TOKEN": "test-token", "GITHUB_REPOSITORY": "owner/repo"},
    )
    def test_bot_comment_only_times_out(self, temp_project, mock_kit_client, mock_github_client):
        """With only the skill's own draft comment, nothing is sent and the run times out."""
        draft = DraftResponse(
            preview_url="https://app.kit.com/publishers/test-pub-123/drafts/draft-456",
            draft_id="draft-456",
        )
        mock_kit_client.create_draft = Mock(return_value=draft)
        mock_kit_client.send_draft = Mock()
        mock_kit_client.get_signup_url = Mock(return_value="https://test-pub-123.kit.com/subscribe")
        mock_kit_client.update_signup_url_in_config = Mock()

        bot_time = datetime.now(UTC)
        mock_github_client.has_label = Mock(return_value=False)
        mock_github_client._run_gh = Mock(
            return_value=json.dumps(
                {
                    "comments": [
                        {
                            "body": "Add the `newsletter:approve` label or comment it to send.",
                            "createdAt": bot_time.isoformat(),
                        }
                    ]
                }
            )
        )
        mock_github_client.add_label = Mock()
        mock_github_client.add_comment = Mock()

        with (
            patch.object(_draft_newsletter_module, "KitClient", return_value=mock_kit_client),
            patch.object(_draft_newsletter_module, "GitHubIssueClient", return_value=mock_github_client),
            patch.object(_draft_newsletter_module, "get_kit_api_key", return_value="test-api-key"),
        ):
            result = run(
                VIDEO_ISSUE,
                VIDEO_PROJECT,
                NEWSLETTER_PROJECT,
                approval_poll_interval=0.01,
                approval_timeout=0.05,
            )

        assert result["sent"] is False
        mock_kit_client.send_draft.assert_not_called()
        labels = [call.args[1] for call in mock_github_client.add_label.call_args_list]
        assert labels == ["newsletter:draft", "newsletter:timeout"]

    def test_wait_for_approval_label_immediate(self, mock_github_client):
        """The owner's label ends the wait at once."""
        mock_github_client.has_label = Mock(return_value=True)
        mock_github_client.has_approval_comment = Mock(return_value=False)

        assert wait_for_approval_label(mock_github_client, VIDEO_ISSUE, poll_interval=1, timeout=5) is True
        mock_github_client.has_label.assert_called_once_with(VIDEO_ISSUE, "newsletter:approve")

    def test_wait_for_approval_comment(self, mock_github_client):
        """The owner's comment also counts as a yes."""
        mock_github_client.has_label = Mock(return_value=False)
        mock_github_client.has_approval_comment = Mock(return_value=True)

        assert wait_for_approval_label(mock_github_client, VIDEO_ISSUE, poll_interval=1, timeout=5) is True
        mock_github_client.has_approval_comment.assert_called_once_with(VIDEO_ISSUE, "newsletter:approve", since=None)

    def test_bot_draft_comment_does_not_approve(self, mock_github_client):
        """The skill's own draft comment must never count as the owner's yes."""
        bot_time = datetime.now(UTC) - timedelta(minutes=5)
        mock_github_client._run_gh = Mock(
            return_value=json.dumps(
                {
                    "comments": [
                        {
                            "body": "Add the `newsletter:approve` label or comment it to send.",
                            "createdAt": bot_time.isoformat().replace("+00:00", "Z"),
                            "authorAssociation": "MEMBER",
                        }
                    ]
                }
            )
        )

        since = datetime.now(UTC)
        assert mock_github_client.has_approval_comment(VIDEO_ISSUE, "newsletter:approve", since=since) is False

    def test_owner_comment_after_draft_approves(self, mock_github_client):
        """An owner comment after the draft counts as the yes."""
        owner_time = datetime.now(UTC) + timedelta(minutes=1)
        mock_github_client._run_gh = Mock(
            return_value=json.dumps(
                {
                    "comments": [
                        {
                            "body": "newsletter:approve",
                            "createdAt": owner_time.isoformat().replace("+00:00", "Z"),
                            "authorAssociation": "OWNER",
                        }
                    ]
                }
            )
        )

        since = datetime.now(UTC)
        assert mock_github_client.has_approval_comment(VIDEO_ISSUE, "newsletter:approve", since=since) is True

    def test_non_member_comment_does_not_approve(self, mock_github_client):
        """A comment from someone without write access is not the owner's yes."""
        owner_time = datetime.now(UTC) + timedelta(minutes=1)
        mock_github_client._run_gh = Mock(
            return_value=json.dumps(
                {
                    "comments": [
                        {
                            "body": "newsletter:approve",
                            "createdAt": owner_time.isoformat().replace("+00:00", "Z"),
                            "authorAssociation": "NONE",
                        }
                    ]
                }
            )
        )

        since = datetime.now(UTC)
        assert mock_github_client.has_approval_comment(VIDEO_ISSUE, "newsletter:approve", since=since) is False

    def test_wait_for_approval_label_timeout(self, mock_github_client):
        """No label and no comment means no approval."""
        mock_github_client.has_label = Mock(return_value=False)
        mock_github_client.has_approval_comment = Mock(return_value=False)

        assert wait_for_approval_label(mock_github_client, VIDEO_ISSUE, poll_interval=0.01, timeout=0.05) is False

    def test_template_variables_rendered(self):
        """Every template variable appears in the rendered newsletter."""
        rendered = render_newsletter(
            {
                "video_title": "Title",
                "video_url": "https://video",
                "script_summary": "Summary",
                "key_points": ["Point one", "Point two"],
                "citations": "Citations",
                "signup_url": "https://signup",
                "unsubscribe_url": "{{ unsubscribe_url }}",
            }
        )

        for value in ("Title", "https://video", "Summary", "Point one", "Citations", "https://signup"):
            assert value in rendered

    def test_exit_codes(self):
        """Exit codes follow the coding rule."""
        assert _exit_code(FileNotFoundError("x")) == 2
        assert _exit_code(KeyError("x")) == 2
        assert _exit_code(ValueError("x")) == 2
        assert _exit_code(RuntimeError("x")) == 1
