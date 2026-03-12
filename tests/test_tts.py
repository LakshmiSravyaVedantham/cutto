"""Tests for the TTS service using real edge-tts calls."""

import os
import tempfile

import pytest

from backend.services.tts import synthesize_to_file


@pytest.mark.asyncio
async def test_synthesize_creates_file_with_content():
    """synthesize_to_file should create a non-empty audio file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_output.mp3")
        result = await synthesize_to_file("Hello world", output_path)

        assert result == output_path
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0


@pytest.mark.asyncio
async def test_synthesize_with_custom_voice():
    """synthesize_to_file should work with a different voice."""
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
