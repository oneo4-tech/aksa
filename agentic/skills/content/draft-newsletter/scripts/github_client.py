"""GitHub Issue client for the draft-newsletter skill.

Uses the `gh` CLI subprocess for authentication and API calls.
"""

import json
import subprocess
from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True)
class Issue:
    """Represents a GitHub issue."""

    number: int
    title: str
    labels: list[str]
    body: str | None


class GitHubIssueClient:
    """Client for interacting with GitHub issues using the `gh` CLI."""

    def __init__(self, repo: str, token: str) -> None:
        """
        Initialize the GitHub issue client.

        Args:
            repo: The repository in format "owner/repo".
            token: GitHub token for authentication (passed via GH_TOKEN env).
        """
        self.repo = repo
        self.token = token

    def _run_gh(self, args: list[str]) -> str:
        """
        Run a `gh` CLI command and return stdout.

        Args:
            args: Arguments to pass to `gh` (e.g., ["issue", "view", "123", "--json", "labels"]).

        Returns:
            The stdout of the command as a string.

        Raises:
            subprocess.CalledProcessError: If the command fails.
        """
        env = {"GH_TOKEN": self.token}
        cmd = ["gh", *args, "--repo", self.repo]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            env={**subprocess.os.environ, **env},
        )
        return result.stdout.strip()

    def get_issue(self, number: int) -> Issue:
        """
        Get a GitHub issue by number.

        Args:
            number: The issue number.

        Returns:
            Issue object with number, title, labels, and body.
        """
        output = self._run_gh(
            [
                "issue",
                "view",
                str(number),
                "--json",
                "number,title,labels,body",
            ]
        )
        data = json.loads(output)
        labels = [label["name"] for label in data.get("labels", [])]
        return Issue(
            number=data["number"],
            title=data["title"],
            labels=labels,
            body=data.get("body"),
        )

    def has_label(self, number: int, label: str) -> bool:
        """
        Check if an issue has a specific label.

        Args:
            number: The issue number.
            label: The label name to check for.

        Returns:
            True if the issue has the label, False otherwise.
        """
        issue = self.get_issue(number)
        return label in issue.labels

    def add_label(self, number: int, label: str) -> None:
        """
        Add a label to a GitHub issue.

        Args:
            number: The issue number.
            label: The label to add.
        """
        self._run_gh(["issue", "edit", str(number), "--add-label", label])

    def add_comment(self, number: int, body: str) -> None:
        """
        Add a comment to a GitHub issue.

        Args:
            number: The issue number.
            body: The comment body.
        """
        self._run_gh(["issue", "comment", str(number), "--body", body])

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        pass
