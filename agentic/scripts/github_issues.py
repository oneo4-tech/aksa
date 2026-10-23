"""The thin layer over the gh CLI for GitHub issues and labels, shared by the issue scripts.

Not a command: factory_issue.py and content_issue.py import it, and tests replace GitHub with a fake.
"""

import json
import subprocess


class GitHubError(Exception):
    """A gh call failed; the scripts exit 1."""


class GitHub:
    """The thin layer over the gh CLI; tests replace it with a fake."""

    def _gh(self, *args: str, stdin: str | None = None) -> str:
        result = subprocess.run(["gh", *args], input=stdin, capture_output=True, text=True, check=False)
        if result.returncode:
            raise GitHubError(f"gh {' '.join(args[:2])} failed: {result.stderr.strip()}")
        return result.stdout

    def issue(self, number: int) -> dict:
        fields = "number,title,state,body,labels,comments"
        data = json.loads(self._gh("issue", "view", str(number), "--json", fields))
        data["labels"] = [label["name"] for label in data["labels"]]
        data["comments"] = [comment["body"] for comment in data["comments"]]
        return data

    def open_issues(self) -> list[dict]:
        data = json.loads(
            self._gh("issue", "list", "--state", "open", "--limit", "500", "--json", "number,title,labels,body")
        )
        return [{**issue, "labels": [label["name"] for label in issue["labels"]]} for issue in data]

    def create(self, title: str, body: str, labels: list[str]) -> int:
        flags = [flag for label in labels for flag in ("--label", label)]
        url = self._gh("issue", "create", "--title", title, "--body-file", "-", *flags, stdin=body).strip()
        return int(url.rsplit("/", 1)[1])

    def edit(
        self,
        number: int,
        body: str | None = None,
        title: str | None = None,
        add: list[str] | None = None,
        remove: list[str] | None = None,
    ) -> None:
        args = ["issue", "edit", str(number)]
        args += ["--body-file", "-"] if body is not None else []
        args += ["--title", title] if title is not None else []
        args += [flag for label in add or [] for flag in ("--add-label", label)]
        args += [flag for label in remove or [] for flag in ("--remove-label", label)]
        self._gh(*args, stdin=body)

    def comment(self, number: int, text: str) -> None:
        self._gh("issue", "comment", str(number), "--body-file", "-", stdin=text)

    def add_sub_issue(self, parent: int, child: int) -> None:
        """Link child as a sub-issue of parent; the REST API takes the child's id, not its number."""
        child_id = self._gh("api", f"repos/{{owner}}/{{repo}}/issues/{child}", "--jq", ".id").strip()
        self._gh(
            "api",
            "--method",
            "POST",
            f"repos/{{owner}}/{{repo}}/issues/{parent}/sub_issues",
            "-F",
            f"sub_issue_id={child_id}",
        )

    def labels(self) -> dict[str, tuple[str, str]]:
        data = json.loads(self._gh("label", "list", "--limit", "500", "--json", "name,color,description"))
        return {label["name"]: (label["color"].lower(), label["description"] or "") for label in data}

    def save_label(self, name: str, color: str, description: str, exists: bool) -> None:
        self._gh("label", "edit" if exists else "create", name, "--color", color, "--description", description)
