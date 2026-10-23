"""Mocked integration tests for the Kit client."""

import importlib.util
import os
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import httpx
import pytest
import yaml

# Load the kit_client module from the hyphenated directory
_kit_client_path = (
    Path(__file__).resolve().parents[1]
    / "agentic"
    / "skills"
    / "content"
    / "draft-newsletter"
    / "scripts"
    / "kit_client.py"
)
_spec = importlib.util.spec_from_file_location("kit_client", _kit_client_path)
_kit_client_module = importlib.util.module_from_spec(_spec)
sys.modules["kit_client"] = _kit_client_module
_spec.loader.exec_module(_kit_client_module)

KitClient = _kit_client_module.KitClient
DraftResponse = _kit_client_module.DraftResponse
SendResponse = _kit_client_module.SendResponse


class TestKitClient:
    """Tests for KitClient using mocked httpx."""

    @pytest.fixture
    def client(self) -> KitClient:
        """Create a KitClient instance for testing."""
        return KitClient(api_key="test-api-key", publication_id="test-pub-123")

    @pytest.fixture
    def mock_response(self) -> Mock:
        """Create a mock httpx response."""
        response = Mock(spec=httpx.Response)
        response.raise_for_status = Mock()
        return response

    def test_kit_create_draft(self, client: KitClient, mock_response: Mock) -> None:
        """
        Test that create_draft calls POST /publications/{id}/drafts
        and returns a DraftResponse with preview_url and draft_id.
        """
        # Arrange
        mock_response.json.return_value = {
            "id": "draft-456",
            "preview_url": "https://app.kit.com/publishers/test-pub-123/drafts/draft-456",
        }
        mock_response.status_code = 201

        with patch.object(client._client, "post", return_value=mock_response) as mock_post:
            # Act
            result = client.create_draft(
                html="<html><body>Test content</body></html>",
                subject="Test Newsletter",
            )

            # Assert
            mock_post.assert_called_once_with(
                "/publications/test-pub-123/drafts",
                json={
                    "html": "<html><body>Test content</body></html>",
                    "subject": "Test Newsletter",
                },
            )
            assert isinstance(result, DraftResponse)
            assert result.draft_id == "draft-456"
            assert result.preview_url == "https://app.kit.com/publishers/test-pub-123/drafts/draft-456"

    def test_kit_send_draft_immediate(self, client: KitClient, mock_response: Mock) -> None:
        """
        Test that send_draft calls POST /drafts/{draft_id}/send
        without send_at for immediate send.
        """
        # Arrange
        mock_response.json.return_value = {"success": True}
        mock_response.status_code = 200

        with patch.object(client._client, "post", return_value=mock_response) as mock_post:
            # Act
            result = client.send_draft(draft_id="draft-456")

            # Assert
            mock_post.assert_called_once_with(
                "/drafts/draft-456/send",
                json=None,
            )
            assert isinstance(result, SendResponse)
            assert result.success is True
            assert result.message == "Draft sent successfully"

    def test_kit_send_draft_scheduled(self, client: KitClient, mock_response: Mock) -> None:
        """
        Test that send_draft calls POST /drafts/{draft_id}/send
        with send_at for scheduled send.
        """
        # Arrange
        mock_response.json.return_value = {"success": True}
        mock_response.status_code = 200
        send_at = datetime(2026, 10, 25, 10, 0, 0)

        with patch.object(client._client, "post", return_value=mock_response) as mock_post:
            # Act
            result = client.send_draft(draft_id="draft-456", send_at=send_at)

            # Assert
            mock_post.assert_called_once_with(
                "/drafts/draft-456/send",
                json={"send_at": "2026-10-25T10:00:00"},
            )
            assert isinstance(result, SendResponse)
            assert result.success is True
            assert "2026-10-25T10:00:00" in result.message

    def test_signup_url_generation(self, client: KitClient) -> None:
        """
        Test that get_signup_url produces a signup URL
        from the publication ID.
        """
        # Act
        signup_url = client.get_signup_url()

        # Assert
        assert signup_url == "https://test-pub-123.kit.com/subscribe"
        assert signup_url.startswith("https://")
        assert ".kit.com/subscribe" in signup_url

    def test_signup_url_from_different_publication(self) -> None:
        """
        Test that signup URL changes with different publication_id.
        """
        # Arrange
        client = KitClient(api_key="test-key", publication_id="my-newsletter")

        # Act
        signup_url = client.get_signup_url()

        # Assert
        assert signup_url == "https://my-newsletter.kit.com/subscribe"

    def test_create_draft_raises_on_error(self, client: KitClient) -> None:
        """
        Test that create_draft raises HTTPStatusError on API error.
        """
        # Arrange
        mock_response = Mock(spec=httpx.Response)
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "401 Unauthorized",
            request=Mock(),
            response=mock_response,
        )
        mock_response.status_code = 401

        with (
            patch.object(client._client, "post", return_value=mock_response),
            pytest.raises(httpx.HTTPStatusError),
        ):
            client.create_draft(html="<html>Test</html>", subject="Test")

    def test_send_draft_raises_on_error(self, client: KitClient) -> None:
        """
        Test that send_draft raises HTTPStatusError on API error.
        """
        # Arrange
        mock_response = Mock(spec=httpx.Response)
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404 Not Found",
            request=Mock(),
            response=mock_response,
        )
        mock_response.status_code = 404

        with (
            patch.object(client._client, "post", return_value=mock_response),
            pytest.raises(httpx.HTTPStatusError),
        ):
            client.send_draft(draft_id="invalid-draft")

    def test_client_context_manager(self) -> None:
        """Test that KitClient works as a context manager."""
        with KitClient(api_key="test-key", publication_id="test-pub") as client:
            assert isinstance(client, KitClient)
            assert client.api_key == "test-key"
            assert client.publication_id == "test-pub"

    def test_client_close(self, client: KitClient) -> None:
        """Test that close() calls the underlying client's close."""
        with patch.object(client._client, "close") as mock_close:
            client.close()
            mock_close.assert_called_once()

    def test_update_signup_url_in_config(self, tmp_path) -> None:
        """
        Test that update_signup_url_in_config writes the signup URL to the project config.

        This verifies AC7: signup URL is produced AND written to config.
        """
        # Arrange: create a temporary project config
        project_slug = "test-newsletter"
        config_dir = tmp_path / ".projects" / "content" / project_slug
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config.yaml"
        initial_config = {
            "platform": "kit",
            "publication_id": "test-pub-123",
            "sender_name": "Test Sender",
            "sender_email": "test@example.com",
            "signup_url": "https://old-signup-url.com/subscribe",
        }
        config_file.write_text(yaml.dump(initial_config, sort_keys=False))

        client = KitClient(api_key="test-api-key", publication_id="test-pub-123")

        # Change to tmp_path so relative path works
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            # Act
            client.update_signup_url_in_config(project_slug)

            # Assert: verify the config file was updated
            with config_file.open("r") as f:
                updated_config = yaml.safe_load(f)

            assert updated_config["signup_url"] == "https://test-pub-123.kit.com/subscribe"
            # Other fields should remain unchanged
            assert updated_config["platform"] == "kit"
            assert updated_config["publication_id"] == "test-pub-123"
            assert updated_config["sender_name"] == "Test Sender"
            assert updated_config["sender_email"] == "test@example.com"
        finally:
            os.chdir(old_cwd)

    def test_update_signup_url_in_config_different_publication(self, tmp_path) -> None:
        """
        Test that update_signup_url_in_config uses the client's publication_id.
        """
        # Arrange
        project_slug = "test-newsletter"
        config_dir = tmp_path / ".projects" / "content" / project_slug
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config.yaml"
        initial_config = {
            "platform": "kit",
            "publication_id": "different-pub",
            "sender_name": "Test Sender",
            "sender_email": "test@example.com",
            "signup_url": "https://old-signup-url.com/subscribe",
        }
        config_file.write_text(yaml.dump(initial_config, sort_keys=False))

        # Client has a different publication_id than the config
        client = KitClient(api_key="test-api-key", publication_id="my-newsletter")

        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            # Act
            client.update_signup_url_in_config(project_slug)

            # Assert: signup URL should use the client's publication_id
            with config_file.open("r") as f:
                updated_config = yaml.safe_load(f)

            assert updated_config["signup_url"] == "https://my-newsletter.kit.com/subscribe"
        finally:
            os.chdir(old_cwd)

    def test_update_signup_url_in_config_raises_on_missing(self, client: KitClient) -> None:
        """
        Test that FileNotFoundError is raised when config doesn't exist.
        """
        with pytest.raises(FileNotFoundError):
            client.update_signup_url_in_config("nonexistent-newsletter")
