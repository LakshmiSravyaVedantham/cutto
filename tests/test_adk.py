"""Tests for the ADK agent wrapper."""

import pytest


def test_root_agent_importable():
    """root_agent can be imported without errors."""
    from backend.adk_agent import root_agent

    assert root_agent is not None


def test_agent_name():
    """Agent has the expected name."""
    from backend.adk_agent import root_agent

    assert root_agent.name == "cutto_director"


def test_agent_model():
    """Agent targets gemini-2.0-flash."""
    from backend.adk_agent import root_agent

    assert root_agent.model == "gemini-2.0-flash"


def test_agent_has_three_tools():
    """Agent has exactly three tools registered."""
    from backend.adk_agent import root_agent

    assert len(root_agent.tools) == 3


def test_tool_names():
    """The three tools have the correct function names."""
    from backend.adk_agent import root_agent

    tool_names = {t.__name__ for t in root_agent.tools}
    assert tool_names == {"plan_video", "get_pipeline_status", "list_video_categories"}


def test_list_video_categories_returns_categories():
    """list_video_categories returns a well-formed dict."""
    from backend.adk_agent import list_video_categories

    result = list_video_categories()
    assert result["status"] == "ok"
    assert isinstance(result["categories"], list)
    assert result["total"] == len(result["categories"])
    assert result["total"] > 0

    # Each category should have required keys
    for cat in result["categories"]:
        assert "id" in cat
        assert "name" in cat
        assert "description" in cat
        assert "example" in cat


def test_get_pipeline_status_not_found():
    """get_pipeline_status returns not_found for unknown video_id."""
    from backend.adk_agent import get_pipeline_status

    result = get_pipeline_status("nonexistent-id")
    assert result["status"] == "not_found"
    assert "nonexistent-id" in result["message"]


def test_agent_instruction_is_system_prompt():
    """Agent instruction matches the SYSTEM_PROMPT from agent.py."""
    from backend.adk_agent import root_agent
    from backend.agent import SYSTEM_PROMPT

    assert root_agent.instruction == SYSTEM_PROMPT


def test_agent_description_is_nonempty():
    """Agent has a meaningful description."""
    from backend.adk_agent import root_agent

    assert len(root_agent.description) > 20
