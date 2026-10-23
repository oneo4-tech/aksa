"""Tests for the newsletter config loader."""

import importlib.util
import os
import sys
from pathlib import Path

import pytest

# Load the config module from the hyphenated directory
_config_path = Path(__file__).resolve().parents[1] / "agentic" / "skills" / "content" / "draft-newsletter" / "config.py"
_spec = importlib.util.spec_from_file_location("draft_newsletter_config", _config_path)
_config_module = importlib.util.module_from_spec(_spec)
sys.modules["draft_newsletter_config"] = _config_module
_spec.loader.exec_module(_config_module)

NewsletterConfig = _config_module.NewsletterConfig
load_newsletter_config = _config_module.load_newsletter_config
get_kit_api_key = _config_module.get_kit_api_key


class TestNewsletterConfig:
    """Tests for NewsletterConfig dataclass."""

    def test_newsletter_config_creation(self):
        """Test that NewsletterConfig can be created with all fields."""
        config = NewsletterConfig(
            platform="kit",
            publication_id="test-id",
            sender_name="Test Sender",
            sender_email="test@example.com",
            signup_url="https://example.com/signup",
        )
        assert config.platform == "kit"
        assert config.publication_id == "test-id"
        assert config.sender_name == "Test Sender"
        assert config.sender_email == "test@example.com"
        assert config.signup_url == "https://example.com/signup"

    def test_newsletter_config_immutable(self):
        """Test that NewsletterConfig is frozen (immutable)."""
        config = NewsletterConfig(
            platform="kit",
            publication_id="test-id",
            sender_name="Test Sender",
            sender_email="test@example.com",
            signup_url="https://example.com/signup",
        )
        with pytest.raises(AttributeError):
            config.platform = "other"


class TestLoadNewsletterConfig:
    """Tests for load_newsletter_config function."""

    def test_load_valid_config(self, tmp_path):
        """Test loading a valid config file."""
        config_dir = tmp_path / ".projects" / "content" / "test-newsletter"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config.yaml"
        config_file.write_text(
            "platform: kit\n"
            "publication_id: test-pub\n"
            "sender_name: Test Sender\n"
            "sender_email: test@example.com\n"
            "signup_url: https://example.com/signup\n"
        )

        # Change to tmp_path so relative path works
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            config = load_newsletter_config("test-newsletter")
            assert config.platform == "kit"
            assert config.publication_id == "test-pub"
            assert config.sender_name == "Test Sender"
            assert config.sender_email == "test@example.com"
            assert config.signup_url == "https://example.com/signup"
        finally:
            os.chdir(old_cwd)

    def test_load_config_missing_file(self):
        """Test that FileNotFoundError is raised for missing config."""
        with pytest.raises(FileNotFoundError):
            load_newsletter_config("nonexistent-newsletter")

    def test_load_config_missing_field(self, tmp_path):
        """Test that ValueError is raised for missing required field."""
        config_dir = tmp_path / ".projects" / "content" / "test-newsletter"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config.yaml"
        config_file.write_text(
            "platform: kit\n"
            "publication_id: test-pub\n"
            "# sender_name is missing\n"
            "sender_email: test@example.com\n"
            "signup_url: https://example.com/signup\n"
        )

        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            with pytest.raises(ValueError, match="Missing required field: sender_name"):
                load_newsletter_config("test-newsletter")
        finally:
            os.chdir(old_cwd)

    def test_load_config_empty_field(self, tmp_path):
        """Test that ValueError is raised for empty required field."""
        config_dir = tmp_path / ".projects" / "content" / "test-newsletter"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config.yaml"
        config_file.write_text(
            "platform: kit\n"
            "publication_id: test-pub\n"
            "sender_name: \n"
            "sender_email: test@example.com\n"
            "signup_url: https://example.com/signup\n"
        )

        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            with pytest.raises(ValueError, match="Field 'sender_name' cannot be empty"):
                load_newsletter_config("test-newsletter")
        finally:
            os.chdir(old_cwd)

    def test_load_config_invalid_platform(self, tmp_path):
        """Test that ValueError is raised for unsupported platform."""
        config_dir = tmp_path / ".projects" / "content" / "test-newsletter"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config.yaml"
        config_file.write_text(
            "platform: mailchimp\n"
            "publication_id: test-pub\n"
            "sender_name: Test Sender\n"
            "sender_email: test@example.com\n"
            "signup_url: https://example.com/signup\n"
        )

        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            with pytest.raises(ValueError, match="Unsupported platform: mailchimp"):
                load_newsletter_config("test-newsletter")
        finally:
            os.chdir(old_cwd)

    def test_load_config_invalid_yaml(self, tmp_path):
        """Test that TypeError is raised for invalid YAML (not a mapping)."""
        config_dir = tmp_path / ".projects" / "content" / "test-newsletter"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config.yaml"
        config_file.write_text("- item1\n- item2\n")

        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            with pytest.raises(TypeError, match="Config file must contain a YAML mapping"):
                load_newsletter_config("test-newsletter")
        finally:
            os.chdir(old_cwd)


class TestGetKitApiKey:
    """Tests for get_kit_api_key function."""

    def test_get_kit_api_key_success(self, monkeypatch):
        """Test getting the API key when set."""
        monkeypatch.setenv("KIT_API_KEY", "test-api-key-123")
        assert get_kit_api_key() == "test-api-key-123"

    def test_get_kit_api_key_missing(self, monkeypatch):
        """Test that KeyError is raised when KIT_API_KEY is not set."""
        monkeypatch.delenv("KIT_API_KEY", raising=False)
        with pytest.raises(KeyError, match="KIT_API_KEY environment variable is not set"):
            get_kit_api_key()
