"""Tests for the ADK multi-agent wrapper."""

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


def test_agent_has_four_tools():
    """Root agent has exactly four tools registered."""
    from backend.adk_agent import root_agent

    assert len(root_agent.tools) == 4


def test_tool_names():
    """The four tools have the correct function names."""
    from backend.adk_agent import root_agent

    tool_names = {t.__name__ for t in root_agent.tools}
    assert tool_names == {"plan_video", "get_pipeline_status", "list_video_categories", "revise_scene"}


def test_list_video_categories_returns_categories():
    """list_video_categories returns a well-formed dict."""
    from backend.adk_agent import list_video_categories

    result = list_video_categories()
    assert result["status"] == "ok"
    assert isinstance(result["categories"], list)
    assert result["total"] == len(result["categories"])
    assert result["total"] > 0

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


def test_sub_agents_exist():
    """Root agent has two sub-agents."""
    from backend.adk_agent import root_agent

    assert hasattr(root_agent, "sub_agents")
    assert len(root_agent.sub_agents) == 2


def test_sub_agent_names():
    """Sub-agents have expected names."""
    from backend.adk_agent import root_agent

    names = {a.name for a in root_agent.sub_agents}
    assert names == {"creative_director", "storyboard_artist"}


def test_revise_scene_not_found():
    """revise_scene returns not_found for unknown video_id."""
    from backend.adk_agent import revise_scene

    result = revise_scene("nonexistent-id", 1, "make it dramatic")
    assert result["status"] == "not_found"


def test_director_agent_importable():
    """Director sub-agent can be imported."""
    from backend.adk_agent import director_agent

    assert director_agent.name == "creative_director"


def test_storyboard_agent_importable():
    """Storyboard sub-agent can be imported."""
    from backend.adk_agent import storyboard_agent

    assert storyboard_agent.name == "storyboard_artist"
