"""Tests for the TTS service."""

import os
import tempfile
from unittest.mock import AsyncMock, patch

import pytest

from backend.services.tts import synthesize_to_file


@pytest.mark.asyncio
@patch("backend.services.tts._cloud_tts_available", False)
@patch("backend.services.tts.edge_tts.Communicate")
async def test_synthesize_creates_file_with_content(mock_communicate):
    """synthesize_to_file should create a non-empty audio file."""
    communicate = mock_communicate.return_value

    async def fake_save(path):
        with open(path, "wb") as f:
            f.write(b"fake-mp3")

    communicate.save = AsyncMock(side_effect=fake_save)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_output.mp3")
        result = await synthesize_to_file("Hello world", output_path)

        assert result == output_path
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0


@pytest.mark.asyncio
@patch("backend.services.tts._cloud_tts_available", False)
@patch("backend.services.tts.edge_tts.Communicate")
async def test_synthesize_with_custom_voice(mock_communicate):
    """synthesize_to_file should work with a different voice."""
    communicate = mock_communicate.return_value

    async def fake_save(path):
        with open(path, "wb") as f:
            f.write(b"fake-mp3")

    communicate.save = AsyncMock(side_effect=fake_save)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "custom_voice.mp3")
        result = await synthesize_to_file(
            "Testing a custom voice",
            output_path,
            voice="en-US-GuyNeural",
        )

        assert result == output_path
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0
        mock_communicate.assert_called_with("Testing a custom voice", "en-US-GuyNeural")
