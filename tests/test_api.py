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
    assert resp.status_code == 404
    data = resp.json()
    assert data["error"] == "Video not found"


def test_video_served_from_gcs_when_local_missing(client):
    with patch("backend.main.storage.download_video", return_value=b"video-bytes"):
        resp = client.get("/videos/test-video/final.mp4")

    assert resp.status_code == 200
    assert resp.headers["content-type"] == "video/mp4"
    assert resp.content == b"video-bytes"


def test_config_lists_new_features(client):
    resp = client.get("/api/config")
    data = resp.json()
    assert data["features"]["image_upload"] is True
    assert data["features"]["crossfade_transitions"] is True
    assert data["features"]["ai_prompt_enhancement"] is True
    assert data["features"]["scene_thumbnails"] is True
    assert data["features"]["quick_start_templates"] is True


def test_plan_endpoint_missing_description(client):
    resp = client.post("/api/plan", json={})
    assert resp.status_code == 400
    assert "description" in resp.json()["error"].lower()


def test_plan_endpoint_calls_adk(client):
    mock_result = {
        "status": "ok",
        "video_id": "test-123",
        "plan": {"title": "Test"},
        "message": "Created plan",
    }
    with patch("backend.adk_agent.plan_video", return_value=mock_result) as mock_pv:
        resp = client.post("/api/plan", json={"description": "Test video"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    mock_pv.assert_called_once_with("Test video")


def test_agent_info_endpoint(client):
    resp = client.get("/api/agent")
    assert resp.status_code == 200
    data = resp.json()
    assert data["architecture"] == "multi-agent"
    assert data["framework"] == "Google ADK"
    assert data["specialty"] == "Kids' educational content (ages 6-12)"
    root = data["root_agent"]
    assert root["name"] == "cutto_director"
    assert len(root["sub_agents"]) == 2
    agent_names = {a["name"] for a in root["sub_agents"]}
    assert "creative_director" in agent_names
    assert "storyboard_artist" in agent_names
    assert data["tool_count"] == 4
    # Tools include descriptions from docstrings
    for tool in root["tools"]:
        assert "name" in tool
        assert "description" in tool
        assert len(tool["description"]) > 0


def test_rate_limit_function():
    """Rate limiter allows 3 requests then blocks."""
    from backend.main import check_rate_limit, video_requests

    test_ip = "test-rate-limit-ip"
    video_requests.pop(test_ip, None)  # clean slate

    assert check_rate_limit(test_ip) is True
    assert check_rate_limit(test_ip) is True
    assert check_rate_limit(test_ip) is True
    assert check_rate_limit(test_ip) is False  # 4th request blocked

    # Cleanup
    video_requests.pop(test_ip, None)


def test_config_models_present(client):
    """Config endpoint exposes all model names."""
    resp = client.get("/api/config")
    models = resp.json()["models"]
    assert "conversation" in models
    assert "image_generation" in models
    assert "video_generation" in models
    assert "image_fallback" in models


def test_agent_info_has_description(client):
    """/api/agent includes a prose description of the architecture."""
    resp = client.get("/api/agent")
    data = resp.json()
    assert "description" in data
    assert "3-agent" in data["description"]
    assert "ADK" in data["description"]
