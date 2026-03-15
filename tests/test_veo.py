"""Tests for the Veo video generation service."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from backend.config import VEO_MODEL


@patch("backend.services.veo.get_client")
def test_generate_video_writes_bytes(mock_get_client):
    """generate_video should poll operation and write video bytes to output_path."""
    fake_bytes = b"\x00\x00\x00\x1cftypisom\x00fake-video-data"

    mock_video = MagicMock()
    mock_video.video.video_bytes = fake_bytes

    mock_result = MagicMock()
    mock_result.generated_videos = [mock_video]

    # First poll: not done. Second poll: done.
    mock_operation = MagicMock()
    mock_operation.done = None
    mock_operation.name = "test-op"
    mock_operation.error = None
    mock_operation.result = mock_result

    mock_done_operation = MagicMock()
    mock_done_operation.done = True
    mock_done_operation.error = None
    mock_done_operation.result = mock_result

    mock_client = MagicMock()
    mock_client.models.generate_videos.return_value = mock_operation
    mock_client.operations.get.return_value = mock_done_operation
    mock_get_client.return_value = mock_client

    from backend.services.veo import generate_video

    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "test_output.mp4"
        with patch("backend.services.veo.time.sleep"):  # skip actual sleep
            result = generate_video("a panda walking", str(out), duration_seconds=5)

        assert result == str(out)
        assert out.exists()
        assert out.read_bytes() == fake_bytes

    call_args = mock_client.models.generate_videos.call_args
    assert call_args.kwargs["model"] == VEO_MODEL
    assert "a panda walking" in call_args.kwargs["prompt"]
    assert "seed" not in call_args.kwargs["config"]


@patch("backend.services.veo.get_client")
def test_generate_video_ignores_seed_in_request(mock_get_client):
    """generate_video should not pass seed until the Veo API supports it again."""
    fake_bytes = b"\x00\x00\x00\x1cftypisom\x00fake-video-data"

    mock_video = MagicMock()
    mock_video.video.video_bytes = fake_bytes

    mock_result = MagicMock()
    mock_result.generated_videos = [mock_video]

    mock_operation = MagicMock()
    mock_operation.done = True
    mock_operation.error = None
    mock_operation.result = mock_result

    mock_client = MagicMock()
    mock_client.models.generate_videos.return_value = mock_operation
    mock_get_client.return_value = mock_client

    from backend.services.veo import generate_video

    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "test_output.mp4"
        result = generate_video(
            "a panda walking", str(out), duration_seconds=5, seed=123
        )

    assert result == str(out)
    call_args = mock_client.models.generate_videos.call_args
    assert call_args.kwargs["config"]["duration_seconds"] == 5
    assert "seed" not in call_args.kwargs["config"]


@patch("backend.services.veo.get_client")
def test_generate_video_raises_on_timeout(mock_get_client):
    """generate_video should raise RuntimeError if operation never completes."""
    mock_operation = MagicMock()
    mock_operation.done = None
    mock_operation.name = "test-op"

    mock_client = MagicMock()
    mock_client.models.generate_videos.return_value = mock_operation
    mock_client.operations.get.return_value = mock_operation
    mock_get_client.return_value = mock_client

    from backend.services.veo import generate_video

    with patch("backend.services.veo.time.sleep"):
        with patch("backend.services.veo.time", wraps=__import__("time")) as mock_time:
            mock_time.sleep = MagicMock()
            with pytest.raises(RuntimeError, match="timed out"):
                generate_video("a failing prompt", "/tmp/nope.mp4", duration_seconds=5)


@patch("backend.services.veo.get_client")
def test_generate_video_raises_on_empty_result(mock_get_client):
    """generate_video should raise RuntimeError when Veo returns no videos."""
    mock_result = MagicMock()
    mock_result.generated_videos = []

    mock_operation = MagicMock()
    mock_operation.done = True
    mock_operation.error = None
    mock_operation.result = mock_result

    mock_client = MagicMock()
    mock_client.models.generate_videos.return_value = mock_operation
    mock_get_client.return_value = mock_client

    from backend.services.veo import generate_video

    with patch("backend.services.veo.time.sleep"):
        with pytest.raises(RuntimeError, match="no videos"):
            generate_video("empty result", "/tmp/nope.mp4")
