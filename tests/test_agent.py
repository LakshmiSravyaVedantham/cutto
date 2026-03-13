"""Tests for backend.agent — conversation session and helpers."""

import pytest

from backend.agent import _guess_mime_type, extract_scene_plan, is_approved


# ---------------------------------------------------------------------------
# _guess_mime_type
# ---------------------------------------------------------------------------


class TestGuessMimeType:
    def test_jpeg_magic_bytes(self):
        data = b"\xff\xd8\xff\xe0" + b"\x00" * 100
        assert _guess_mime_type(data) == "image/jpeg"

    def test_png_magic_bytes(self):
        data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        assert _guess_mime_type(data) == "image/png"

    def test_webp_magic_bytes(self):
        data = b"RIFF\x00\x00\x00\x00WEBP" + b"\x00" * 100
        assert _guess_mime_type(data) == "image/webp"

    def test_unknown_defaults_to_jpeg(self):
        data = b"\x00\x01\x02\x03" + b"\x00" * 100
        assert _guess_mime_type(data) == "image/jpeg"

    def test_empty_defaults_to_jpeg(self):
        assert _guess_mime_type(b"") == "image/jpeg"


# ---------------------------------------------------------------------------
# extract_scene_plan
# ---------------------------------------------------------------------------


class TestExtractScenePlan:
    def test_extracts_valid_json(self):
        text = """Here's your plan:
```json
{
  "title": "Test Video",
  "total_scenes": 1,
  "mood": "calm",
  "visual_style_anchor": "test style",
  "scenes": [
    {
      "scene_number": 1,
      "speaker": "narrator",
      "narration": "Hello world",
      "visual_prompt": "A test scene",
      "visual_type": "video",
      "target_duration": 12
    }
  ]
}
```
"""
        plan = extract_scene_plan(text)
        assert plan is not None
        assert plan.title == "Test Video"
        assert len(plan.scenes) == 1
        assert plan.scenes[0].narration == "Hello world"

    def test_returns_none_for_no_json(self):
        assert extract_scene_plan("No JSON here") is None

    def test_returns_none_for_invalid_json(self):
        text = "```json\n{invalid}\n```"
        assert extract_scene_plan(text) is None


# ---------------------------------------------------------------------------
# is_approved
# ---------------------------------------------------------------------------


class TestIsApproved:
    def test_approved_detected(self):
        assert is_approved("APPROVED: Starting video generation now!") is True

    def test_case_insensitive(self):
        assert is_approved("approved: starting") is True

    def test_not_approved(self):
        assert is_approved("Here's your plan, let me know if it looks good.") is False
