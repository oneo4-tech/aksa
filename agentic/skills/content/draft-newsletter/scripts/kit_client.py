"""Kit API client for the draft-newsletter skill."""

from dataclasses import dataclass
from datetime import datetime
from typing import Self

import httpx


def _load_config_module():
    """Load the config module dynamically to avoid relative import issues."""
    import importlib.util
    import sys
    from pathlib import Path

    config_path = Path(__file__).parent / "config.py"
    spec = importlib.util.spec_from_file_location("draft_newsletter_config", config_path)
    config_module = importlib.util.module_from_spec(spec)
    sys.modules["draft_newsletter_config"] = config_module
    spec.loader.exec_module(config_module)
    return config_module


_config_module = _load_config_module()
NewsletterConfig = _config_module.NewsletterConfig
load_newsletter_config = _config_module.load_newsletter_config
save_newsletter_config = _config_module.save_newsletter_config
update_signup_url = _config_module.update_signup_url


@dataclass(frozen=True)
class DraftResponse:
    """Response from creating a draft."""

    preview_url: str
    draft_id: str


@dataclass(frozen=True)
class SendResponse:
    """Response from sending/scheduling a draft."""

    success: bool
    message: str


class KitClient:
    """Client for interacting with the Kit (ConvertKit) API."""

    BASE_URL = "https://api.kit.com/v4"

    def __init__(self, api_key: str, publication_id: str) -> None:
        """
        Initialize the Kit client.

        Args:
            api_key: The Kit API key.
            publication_id: The Kit publication ID.
        """
        self.api_key = api_key
        self.publication_id = publication_id
        self._client = httpx.Client(
            base_url=self.BASE_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    def create_draft(self, html: str, subject: str) -> DraftResponse:
        """
        Create a draft newsletter in Kit.

        Args:
            html: The HTML content of the newsletter.
            subject: The subject line of the newsletter.

        Returns:
            DraftResponse with preview_url and draft_id.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        response = self._client.post(
            f"/publications/{self.publication_id}/drafts",
            json={"html": html, "subject": subject},
        )
        response.raise_for_status()
        data = response.json()

        # Kit API returns draft object with id and preview_url
        draft_id = str(data.get("id", data.get("draft_id", "")))
        preview_url = data.get("preview_url", f"https://app.kit.com/publishers/{self.publication_id}/drafts/{draft_id}")

        return DraftResponse(preview_url=preview_url, draft_id=draft_id)

    def send_draft(self, draft_id: str, send_at: datetime | None = None) -> SendResponse:
        """
        Send or schedule a draft.

        Args:
            draft_id: The ID of the draft to send.
            send_at: Optional datetime to schedule the send. If None, sends immediately.

        Returns:
            SendResponse with success status and message.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        payload = {}
        if send_at is not None:
            payload["send_at"] = send_at.isoformat()

        response = self._client.post(
            f"/drafts/{draft_id}/send",
            json=payload if payload else None,
        )
        response.raise_for_status()

        if send_at:
            return SendResponse(success=True, message=f"Draft scheduled for {send_at.isoformat()}")
        return SendResponse(success=True, message="Draft sent successfully")

    def get_signup_url(self) -> str:
        """
        Get the signup form URL for the publication.

        Returns:
            The signup URL for the publication.
        """
        # Kit signup URLs follow the pattern: https://{subdomain}.kit.com/subscribe
        # For now, construct from publication_id (common pattern)
        # In practice, this could be fetched from publication config or API
        return f"https://{self.publication_id}.kit.com/subscribe"

    def update_signup_url_in_config(self, project_slug: str) -> None:
        """
        Generate the signup URL and write it to the project config.

        Args:
            project_slug: The slug of the newsletter project (e.g., "oneo4-newsletter").

        Raises:
            FileNotFoundError: If the config file doesn't exist.
            ValueError: If required fields are missing or invalid.
        """
        signup_url = self.get_signup_url()
        config = load_newsletter_config(project_slug)
        updated_config = update_signup_url(config, signup_url)
        save_newsletter_config(project_slug, updated_config)

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
