"""Tests for the AKSA OS HTTP routes."""

from aksa_os.app import create_app
from fastapi.testclient import TestClient


def test_overview_answers_with_the_shell():
    client = TestClient(create_app())
    response = client.get("/")
    assert response.status_code == 200
    assert "AKSA OS" in response.text


def test_static_stylesheet_is_served():
    client = TestClient(create_app())
    response = client.get("/static/aksa_os.css")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/css")
