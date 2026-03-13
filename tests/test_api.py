"""Tests for REST API endpoints."""

from unittest.mock import patch

import pytest


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    from backend.main import app

    return TestClient(app)


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "cutto"
    assert "version" in data


def test_categories_endpoint(client):
    resp = client.get("/api/categories")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert isinstance(data["categories"], list)
    assert data["total"] > 0
    # Each category has required keys
    for cat in data["categories"]:
        assert "id" in cat
        assert "name" in cat
        assert "description" in cat
        assert "example" in cat


def test_config_endpoint(client):
    resp = client.get("/api/config")
    assert resp.status_code == 200
    data = resp.json()
    assert "models" in data
    assert "features" in data
    assert "limits" in data
    assert data["features"]["voice_input"] is True
    assert data["limits"]["videos_per_hour"] == 3


def test_video_not_found(client):
    resp = client.get("/videos/nonexistent-id/final.mp4")
    assert resp.status_code == 200
    data = resp.json()
    assert data["error"] == "Video not found"


def test_video_served_from_gcs_when_local_missing(client):
    with patch("backend.main.storage.download_video", return_value=b"video-bytes"):
        resp = client.get("/videos/test-video/final.mp4")

    assert resp.status_code == 200
    assert resp.headers["content-type"] == "video/mp4"
    assert resp.content == b"video-bytes"
