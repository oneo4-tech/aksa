"""CLI entry point for the draft-newsletter skill.

Wires together: config → read script.md/citations.md → compose Markdown
→ write newsletter.md → convert to HTML → Kit create draft → wait for
`newsletter:approve` label → Kit send → apply labels → write the configured signup URL.

Exit codes: 0 done, 1 error, 2 bad input, 3 waiting for the owner.
"""

import importlib.util
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader


def _load_module(name: str, filename: str):
    path = Path(__file__).parent / filename
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_config_module = _load_module("draft_newsletter_config", "config.py")
_markdown_module = _load_module("draft_newsletter_markdown_to_html", "markdown_to_html.py")
_kit_module = _load_module("draft_newsletter_kit_client", "kit_client.py")
_github_module = _load_module("draft_newsletter_github_client", "github_client.py")

NewsletterConfig = _config_module.NewsletterConfig
load_newsletter_config = _config_module.load_newsletter_config
save_newsletter_config = _config_module.save_newsletter_config
update_signup_url = _config_module.update_signup_url
get_kit_api_key = _config_module.get_kit_api_key

convert = _markdown_module.convert

KitClient = _kit_module.KitClient
DraftResponse = _kit_module.DraftResponse

GitHubIssueClient = _github_module.GitHubIssueClient
Issue = _github_module.Issue

DEFAULT_VIDEO_PROJECT = "oneo4-testlab"
DEFAULT_NEWSLETTER_PROJECT = "oneo4-newsletter"
APPROVAL_LABEL = "newsletter:approve"


def video_folder(video_project_slug: str, video_issue_number: int) -> Path:
    """Return the per-video folder under the video project."""
    return Path(f".projects/youtube/{video_project_slug}/videos/{video_issue_number}")


def read_script_and_citations(video_project_slug: str, video_issue_number: int) -> tuple[str, str]:
    """
    Read script.md and citations.md from the video folder.

    Args:
        video_project_slug: The video project slug (e.g., "oneo4-testlab").
        video_issue_number: The GitHub issue number for the video.

    Returns:
        Tuple of (script_content, citations_content).

    Raises:
        FileNotFoundError: If either file is missing.
    """
    folder = video_folder(video_project_slug, video_issue_number)
    script_path = folder / "script.md"
    citations_path = folder / "citations.md"

    if not script_path.exists():
        raise FileNotFoundError(f"script.md not found in {folder}")
    if not citations_path.exists():
        raise FileNotFoundError(f"citations.md not found in {folder}")

    return (
        script_path.read_text(encoding="utf-8"),
        citations_path.read_text(encoding="utf-8"),
    )


def _section_lines(script_content: str, heading: str) -> list[str]:
    """Return the non-empty lines of the section under `## <heading>`."""
    lines = script_content.splitlines()
    collected: list[str] = []
    in_section = False
    for line in lines:
        if line.startswith("## "):
            in_section = line[3:].strip().lower() == heading.lower()
            continue
        if in_section:
            collected.append(line)
    return [line for line in collected if line.strip()]


def extract_metadata(
    script_content: str,
    citations_content: str,
    video_issue_number: int,
    signup_url: str = "",
) -> dict:
    """
    Extract metadata from script and citations for the newsletter template.

    The script follows #28's shape: a title heading, a `**Video URL:**` line,
    a `## Summary` paragraph, and `- ` bullets under `## Key Points`.

    Args:
        script_content: The content of script.md.
        citations_content: The content of citations.md.
        video_issue_number: The video issue number.
        signup_url: The configured signup URL to include.

    Returns:
        Dictionary with template variables.
    """
    video_title = ""
    for line in script_content.splitlines():
        if line.startswith("# "):
            video_title = line[2:].strip()
            break
    if not video_title:
        raise ValueError(f"script.md for issue {video_issue_number} has no title heading")

    video_url = ""
    for line in script_content.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("**video url:**"):
            video_url = stripped[len("**Video URL:**") :].strip()
            break
    if not video_url:
        raise ValueError(f"script.md for issue {video_issue_number} has no **Video URL:** line")

    summary_lines = [
        line.strip() for line in _section_lines(script_content, "Summary") if not line.strip().startswith("#")
    ]
    script_summary = " ".join(summary_lines).strip()

    key_points = [
        line.strip()[2:].strip()
        for line in _section_lines(script_content, "Key Points")
        if line.strip().startswith("- ")
    ]

    unsubscribe_url = "{{ unsubscribe_url }}"

    return {
        "video_title": video_title,
        "video_url": video_url,
        "script_summary": script_summary,
        "key_points": key_points,
        "citations": citations_content,
        "signup_url": signup_url,
        "unsubscribe_url": unsubscribe_url,
    }


def render_newsletter(template_vars: dict) -> str:
    """
    Render the newsletter Markdown using the Jinja2 template.

    Args:
        template_vars: Variables to pass to the template.

    Returns:
        Rendered Markdown string.
    """
    template_dir = Path(__file__).parent.parent / "references" / "templates"
    env = Environment(loader=FileSystemLoader(template_dir), keep_trailing_newline=True)
    template = env.get_template("newsletter.md.j2")
    return template.render(**template_vars)


def write_newsletter_md(newsletter_md: str, video_project_slug: str, video_issue_number: int) -> Path:
    """
    Write the newsletter Markdown to the video folder.

    Args:
        newsletter_md: The rendered Markdown content.
        video_project_slug: The video project slug.
        video_issue_number: The video issue number.

    Returns:
        Path to the written file.
    """
    output_path = video_folder(video_project_slug, video_issue_number) / "newsletter.md"
    output_path.write_text(newsletter_md, encoding="utf-8")
    return output_path


def wait_for_approval_label(
    github_client: GitHubIssueClient,
    video_issue_number: int,
    since: datetime | None = None,
    poll_interval: int = 30,
    timeout: int = 3600,
) -> bool:
    """
    Wait for the owner's yes on the video issue.

    The yes is a `newsletter:approve` label or a comment that contains
    `newsletter:approve` written at or after `since`, so the skill's own
    draft comment never counts as the owner's approval.

    Args:
        github_client: GitHub issue client.
        video_issue_number: The video issue number.
        since: Ignore comments created before this time.
        poll_interval: Seconds between checks.
        timeout: Maximum seconds to wait.

    Returns:
        True if the approval was found, False if timeout.
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        if github_client.has_label(video_issue_number, APPROVAL_LABEL):
            return True
        if github_client.has_approval_comment(video_issue_number, APPROVAL_LABEL, since=since):
            return True
        time.sleep(poll_interval)
    return False


def run(
    video_issue_number: int,
    video_project_slug: str = DEFAULT_VIDEO_PROJECT,
    newsletter_project_slug: str = DEFAULT_NEWSLETTER_PROJECT,
    approval_poll_interval: int = 30,
    approval_timeout: int = 3600,
) -> dict:
    """
    Draft a newsletter from a published video, and send it once the owner says yes.

    Args:
        video_issue_number: The GitHub issue number for the published video.
        video_project_slug: The video project slug (default: "oneo4-testlab").
        newsletter_project_slug: The newsletter project slug (default: "oneo4-newsletter").
        approval_poll_interval: Seconds between approval checks.
        approval_timeout: Maximum seconds to wait for the owner's yes.

    Returns:
        Dictionary with results: draft_id, preview_url, sent, signup_url.

    Raises:
        FileNotFoundError: If config or video files are missing.
        KeyError: If KIT_API_KEY, GH_TOKEN, or GITHUB_REPOSITORY is not set.
        httpx.HTTPStatusError: If Kit API calls fail.
    """
    config = load_newsletter_config(newsletter_project_slug)

    kit_api_key = get_kit_api_key()
    gh_token = os.environ["GH_TOKEN"]
    repo = os.environ["GITHUB_REPOSITORY"]

    script_content, citations_content = read_script_and_citations(video_project_slug, video_issue_number)

    with KitClient(kit_api_key, config.publication_id, config.signup_url) as kit_client:
        signup_url = kit_client.get_signup_url()
        template_vars = extract_metadata(
            script_content,
            citations_content,
            video_issue_number,
            signup_url=signup_url,
        )

        newsletter_md = render_newsletter(template_vars)
        write_newsletter_md(newsletter_md, video_project_slug, video_issue_number)

        newsletter_html = convert(newsletter_md)

        subject = f"Newsletter: {template_vars['video_title']}"
        draft_response = kit_client.create_draft(newsletter_html, subject)
        draft_id = draft_response.draft_id
        preview_url = draft_response.preview_url

        # Write the signup URL back to the newsletter project config (AC7).
        kit_client.update_signup_url_in_config(newsletter_project_slug)

        with GitHubIssueClient(repo, gh_token) as gh_client:
            # A label left by an earlier attempt is not a yes for this draft.
            gh_client.remove_label(video_issue_number, APPROVAL_LABEL)
            gh_client.add_label(video_issue_number, "newsletter:draft")
            gh_client.add_comment(
                video_issue_number,
                f"Newsletter draft created: {preview_url}\n\nAdd the `{APPROVAL_LABEL}` label or comment it to send.",
            )

            # Only comments newer than the draft comment can be the owner's yes.
            # GitHub's clock decides, so a local clock skew cannot self-approve.
            draft_comment_time = gh_client.latest_comment_time(video_issue_number) or datetime.now(UTC)
            approved = wait_for_approval_label(
                gh_client,
                video_issue_number,
                since=draft_comment_time,
                poll_interval=approval_poll_interval,
                timeout=approval_timeout,
            )

            if approved:
                gh_client.add_label(video_issue_number, "newsletter:approved")
                kit_client.send_draft(draft_id)
                gh_client.add_label(video_issue_number, "newsletter:sent")
                gh_client.add_comment(video_issue_number, "Newsletter sent successfully")
                sent = True
            else:
                gh_client.add_label(video_issue_number, "newsletter:timeout")
                gh_client.add_comment(video_issue_number, "Newsletter approval timed out")
                sent = False

    return {
        "draft_id": draft_id,
        "preview_url": preview_url,
        "sent": sent,
        "signup_url": template_vars["signup_url"],
    }


def main(
    video_issue_number: int,
    video_project_slug: str = DEFAULT_VIDEO_PROJECT,
    newsletter_project_slug: str = DEFAULT_NEWSLETTER_PROJECT,
) -> dict:
    """Alias of `run`, kept as the CLI's entry point."""
    return run(video_issue_number, video_project_slug, newsletter_project_slug)


def _exit_code(exc: BaseException) -> int:
    """Map an exception to the CLI exit code."""
    if isinstance(exc, (FileNotFoundError, KeyError, ValueError)):
        return 2
    return 1


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Draft newsletter from video issue")
    parser.add_argument("video_issue_number", type=int, help="GitHub issue number for the video")
    parser.add_argument(
        "--video-project",
        default=DEFAULT_VIDEO_PROJECT,
        help="Video project slug (default: oneo4-testlab)",
    )
    parser.add_argument(
        "--newsletter-project",
        default=DEFAULT_NEWSLETTER_PROJECT,
        help="Newsletter project slug (default: oneo4-newsletter)",
    )
    args = parser.parse_args()

    try:
        result = run(args.video_issue_number, args.video_project, args.newsletter_project)
    except Exception as exc:  # noqa: BLE001 - CLI entry point reports every error
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(_exit_code(exc))

    print(f"Draft ID: {result['draft_id']}")
    print(f"Preview URL: {result['preview_url']}")
    if result["sent"]:
        print("Sent: yes")
        sys.exit(0)
    print(f"Sent: no, waiting for the owner's `{APPROVAL_LABEL}`")
    sys.exit(3)
