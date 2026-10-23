"""Config loader for the draft-newsletter skill."""

import os
from dataclasses import dataclass, replace
from pathlib import Path

import yaml


@dataclass(frozen=True)
class NewsletterConfig:
    """Configuration for a newsletter project."""

    platform: str
    publication_id: str
    sender_name: str
    sender_email: str
    signup_url: str


def load_newsletter_config(project_slug: str) -> NewsletterConfig:
    """
    Load newsletter configuration from the project's config.yaml.

    Args:
        project_slug: The slug of the newsletter project (e.g., "oneo4-newsletter").

    Returns:
        NewsletterConfig with the loaded values.

    Raises:
        FileNotFoundError: If the config file doesn't exist.
        ValueError: If required fields are missing or invalid.
    """
    config_path = Path(f".projects/content/{project_slug}/config.yaml")
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with config_path.open("r") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise TypeError("Config file must contain a YAML mapping")

    required_fields = ["platform", "publication_id", "sender_name", "sender_email", "signup_url"]
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
        if not data[field]:
            raise ValueError(f"Field '{field}' cannot be empty")

    if data["platform"] != "kit":
        raise ValueError(f"Unsupported platform: {data['platform']}. Only 'kit' is supported.")

    return NewsletterConfig(
        platform=data["platform"],
        publication_id=data["publication_id"],
        sender_name=data["sender_name"],
        sender_email=data["sender_email"],
        signup_url=data["signup_url"],
    )


def get_kit_api_key() -> str:
    """
    Get the Kit API key from the environment.

    Returns:
        The KIT_API_KEY value.

    Raises:
        KeyError: If KIT_API_KEY is not set in the environment.
    """
    try:
        return os.environ["KIT_API_KEY"]
    except KeyError:
        raise KeyError("KIT_API_KEY environment variable is not set") from None


def update_signup_url(config: NewsletterConfig, signup_url: str) -> NewsletterConfig:
    """
    Create a new NewsletterConfig with an updated signup URL.

    Since NewsletterConfig is frozen, this uses dataclasses.replace()
    to create a new instance with the updated field.

    Args:
        config: The original NewsletterConfig.
        signup_url: The new signup URL to set.

    Returns:
        A new NewsletterConfig with the updated signup_url.
    """
    return replace(config, signup_url=signup_url)


def save_newsletter_config(project_slug: str, config: NewsletterConfig) -> None:
    """
    Save the newsletter configuration to the project's config.yaml.

    Args:
        project_slug: The slug of the newsletter project.
        config: The NewsletterConfig to save.

    Raises:
        FileNotFoundError: If the config file's directory doesn't exist.
    """
    config_path = Path(f".projects/content/{project_slug}/config.yaml")
    if not config_path.parent.exists():
        raise FileNotFoundError(f"Config directory not found: {config_path.parent}")

    data = {
        "platform": config.platform,
        "publication_id": config.publication_id,
        "sender_name": config.sender_name,
        "sender_email": config.sender_email,
        "signup_url": config.signup_url,
    }

    with config_path.open("w") as f:
        yaml.safe_dump(data, f, sort_keys=False)
