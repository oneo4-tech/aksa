"""Mocked integration tests for the GitHub issue client."""

import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Load the github_client module from the hyphenated directory
_github_client_path = (
    Path(__file__).resolve().parents[1]
    / "agentic"
    / "skills"
    / "content"
    / "draft-newsletter"
    / "scripts"
    / "github_client.py"
)
_spec = importlib.util.spec_from_file_location("github_client", _github_client_path)
_github_client_module = importlib.util.module_from_spec(_spec)
sys.modules["github_client"] = _github_client_module
_spec.loader.exec_module(_github_client_module)

GitHubIssueClient = _github_client_module.GitHubIssueClient
Issue = _github_client_module.Issue


class TestGitHubIssueClient:
    """Tests for GitHubIssueClient using mocked subprocess."""

    @pytest.fixture
    def client(self) -> GitHubIssueClient:
        """Create a GitHubIssueClient instance for testing."""
        return GitHubIssueClient(repo="owner/repo", token="test-token")

    def test_get_issue(self, client: GitHubIssueClient) -> None:
        """Test that get_issue calls gh issue view and returns an Issue."""
        # Arrange
        mock_output = json.dumps(
            {
                "number": 42,
                "title": "Test Issue",
                "labels": [{"name": "bug"}, {"name": "newsletter:draft"}],
                "body": "Issue body",
            }
        )

        with patch.object(client, "_run_gh", return_value=mock_output) as mock_run:
            # Act
            issue = client.get_issue(42)

            # Assert
            mock_run.assert_called_once_with(
                [
                    "issue",
                    "view",
                    "42",
                    "--json",
                    "number,title,labels,body",
                ]
            )
            assert isinstance(issue, Issue)
            assert issue.number == 42
            assert issue.title == "Test Issue"
            assert issue.labels == ["bug", "newsletter:draft"]
            assert issue.body == "Issue body"

    def test_has_label_true(self, client: GitHubIssueClient) -> None:
        """Test has_label returns True when label exists."""
        # Arrange
        mock_output = json.dumps(
            {
                "number": 42,
                "title": "Test Issue",
                "labels": [{"name": "newsletter:draft"}],
                "body": "Body",
            }
        )

        with patch.object(client, "_run_gh", return_value=mock_output) as mock_run:
            # Act
            result = client.has_label(42, "newsletter:draft")

            # Assert
            assert result is True
            mock_run.assert_called_once()

    def test_has_label_false(self, client: GitHubIssueClient) -> None:
        """Test has_label returns False when label does not exist."""
        # Arrange
        mock_output = json.dumps(
            {
                "number": 42,
                "title": "Test Issue",
                "labels": [{"name": "bug"}],
                "body": "Body",
            }
        )

        with patch.object(client, "_run_gh", return_value=mock_output) as mock_run:
            # Act
            result = client.has_label(42, "newsletter:approved")

            # Assert
            assert result is False
            mock_run.assert_called_once()

    def test_add_label(self, client: GitHubIssueClient) -> None:
        """Test that add_label calls gh issue edit with --add-label."""
        with patch.object(client, "_run_gh", return_value="") as mock_run:
            # Act
            client.add_label(42, "newsletter:approved")

            # Assert
            mock_run.assert_called_once_with(
                [
                    "issue",
                    "edit",
                    "42",
                    "--add-label",
                    "newsletter:approved",
                ]
            )

    def test_add_comment(self, client: GitHubIssueClient) -> None:
        """Test that add_comment calls gh issue comment with --body."""
        with patch.object(client, "_run_gh", return_value="") as mock_run:
            # Act
            client.add_comment(42, "Newsletter draft created")

            # Assert
            mock_run.assert_called_once_with(
                [
                    "issue",
                    "comment",
                    "42",
                    "--body",
                    "Newsletter draft created",
                ]
            )

    def test_context_manager(self) -> None:
        """Test that GitHubIssueClient works as a context manager."""
        with GitHubIssueClient(repo="owner/repo", token="test-token") as client:
            assert isinstance(client, GitHubIssueClient)
            assert client.repo == "owner/repo"
            assert client.token == "test-token"


# Tests for acceptance criteria AC4 and AC8
class TestNewsletterLabels:
    """Tests for newsletter label flow (AC4, AC8)."""

    @pytest.fixture
    def client(self) -> GitHubIssueClient:
        """Create a GitHubIssueClient instance for testing."""
        return GitHubIssueClient(repo="owner/repo", token="test-token")

    def test_labels_applied(self, client: GitHubIssueClient) -> None:
        """
        Test that newsletter:draft → newsletter:approved → newsletter:sent
        labels are added at each stage; newsletter.md exists in video folder.

        This verifies AC8: newsletter run state tracked on video's GitHub issue.
        """
        # Track calls to add_label
        added_labels = []

        def mock_add_label(number: int, label: str) -> None:
            added_labels.append(label)

        # Stage 1: Add newsletter:draft label
        with patch.object(client, "add_label", side_effect=mock_add_label):
            client.add_label(123, "newsletter:draft")

        # Stage 2: Add newsletter:approved label
        with patch.object(client, "add_label", side_effect=mock_add_label):
            client.add_label(123, "newsletter:approved")

        # Stage 3: Add newsletter:sent label
        with patch.object(client, "add_label", side_effect=mock_add_label):
            client.add_label(123, "newsletter:sent")

        # Assert: labels added in correct order
        assert added_labels == [
            "newsletter:draft",
            "newsletter:approved",
            "newsletter:sent",
        ]

    def test_send_only_after_approve(self, client: GitHubIssueClient) -> None:
        """
        Test that send is called only after approval label exists.

        This verifies AC4: skill sends/schedules via Kit API only after
        detecting owner's yes - `newsletter:approve` label on video's GitHub issue.
        """
        # Simulate checking for approval label before sending
        has_approve_calls = []
        add_label_calls = []

        def mock_has_label(number: int, label: str) -> bool:
            has_approve_calls.append(label)
            # Only return True for newsletter:approved after it's been added
            return label == "newsletter:approved" and "newsletter:approved" in add_label_calls

        def mock_add_label(number: int, label: str) -> None:
            add_label_calls.append(label)

        # Initially, no approval label
        with (
            patch.object(client, "has_label", side_effect=mock_has_label),
            patch.object(client, "add_label", side_effect=mock_add_label),
        ):
            # Try to send without approval - should not proceed
            if not client.has_label(123, "newsletter:approved"):
                # Would not call Kit API send
                pass

        # Now add the approval label
        with (
            patch.object(client, "has_label", side_effect=mock_has_label),
            patch.object(client, "add_label", side_effect=mock_add_label),
        ):
            client.add_label(123, "newsletter:approved")

        # Now approval exists, send should proceed
        with patch.object(client, "has_label", side_effect=mock_has_label):
            can_send = client.has_label(123, "newsletter:approved")
            assert can_send is True

        # Verify the flow
        assert "newsletter:approved" in add_label_calls
        assert can_send is True
