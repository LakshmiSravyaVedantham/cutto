"""
CutTo ADK Agent — Alternative entry point using Google Agent Development Kit.

This wraps CutTo's video planning logic as proper ADK function tools,
providing an agent that hackathon judges can interact with via the ADK
runner or A2A protocol.

Usage:
    from backend.adk_agent import root_agent

The existing agent.py and main.py are NOT modified — this is additive.
"""

import json
import logging
import uuid
from typing import Optional

from backend.agent import SYSTEM_PROMPT, extract_scene_plan
from backend.models import ScenePlan

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory store for plans created during a session
# ---------------------------------------------------------------------------
_active_plans: dict[str, dict] = {}

# ---------------------------------------------------------------------------
# Video categories supported by CutTo (mirrors SYSTEM_PROMPT)
# ---------------------------------------------------------------------------
VIDEO_CATEGORIES = [
    {
        "id": "story",
        "name": "Story",
        "description": "Animated narrative with characters (Pixar, anime, Ghibli style)",
        "example": "A fox and a rabbit become unlikely friends in a magical forest",
    },
    {
        "id": "explainer",
        "name": "Explainer",
        "description": "Educational video that breaks down a concept step by step (medical, science, tech, finance)",
        "example": "How insulin regulates blood sugar in the human body",
    },
    {
        "id": "documentary",
        "name": "Documentary",
        "description": "Cinematic, real-world footage style, narrator-driven",
        "example": "The rise and fall of the Roman Empire in 2 minutes",
    },
    {
        "id": "tutorial",
        "name": "Tutorial",
        "description": "How-to, step-by-step instructions with visuals",
        "example": "How to set up a Python virtual environment",
    },
    {
        "id": "marketing",
        "name": "Marketing",
        "description": "Product/service showcase, persuasive, polished",
        "example": "Launch video for a new fitness tracking app",
    },
    {
        "id": "motivational",
        "name": "Motivational",
        "description": "Inspiring, speaker-driven, emotional arc",
        "example": "Never give up — a 90-second motivational piece",
    },
]


# ---------------------------------------------------------------------------
# ADK Function Tools
# ---------------------------------------------------------------------------

def plan_video(description: str) -> dict:
    """Take a user's video description and return an 8-scene plan.

    This uses Gemini to generate a structured scene plan based on the
    user's description. The plan includes scenes, narration, visual
    prompts, and speaker assignments following CutTo's format.

    Args:
        description: A natural-language description of the desired video.
                     Example: "Explain how the human heart works for med students"

    Returns:
        A dict with keys: video_id, title, total_scenes, mood,
        visual_style_anchor, scenes (list of scene dicts), and status.
    """
    try:
        from google import genai
        from google.genai import types
        from backend.config import GOOGLE_API_KEY, GEMINI_MODEL

        client = genai.Client(api_key=GOOGLE_API_KEY)

        planning_prompt = (
            f"Create a video plan for: {description}\n\n"
            "Output the complete scene plan as a JSON code block with "
            "exactly 8 scenes following the format in your instructions."
        )

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[{"role": "user", "parts": [{"text": planning_prompt}]}],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
            ),
        )

        if not response.candidates or not response.candidates[0].content.parts:
            return {
                "status": "error",
                "message": "Gemini returned an empty response. Try a more detailed description.",
            }

        text = response.candidates[0].content.parts[0].text
        scene_plan = extract_scene_plan(text)

        if scene_plan:
            plan_dict = scene_plan.model_dump()
            _active_plans[plan_dict["video_id"]] = plan_dict
            return {
                "status": "ok",
                "video_id": plan_dict["video_id"],
                "plan": plan_dict,
                "message": f"Created {scene_plan.total_scenes}-scene plan: '{scene_plan.title}'",
            }

        # Gemini responded but no JSON block was extracted
        return {
            "status": "partial",
            "raw_response": text[:2000],
            "message": "Gemini responded but no structured plan was extracted. The raw response is included.",
        }

    except ImportError as e:
        return {
            "status": "error",
            "message": f"Missing dependency: {e}. Install google-genai.",
        }
    except Exception as e:
        logger.error(f"plan_video failed: {e}", exc_info=True)
        return {
            "status": "error",
            "message": f"Failed to generate plan: {e}",
        }


def get_pipeline_status(video_id: str) -> dict:
    """Return current pipeline status for a given video ID.

    Args:
        video_id: The UUID of the video returned by plan_video.

    Returns:
        A dict with the plan details and current status.
    """
    plan = _active_plans.get(video_id)
    if not plan:
        return {
            "status": "not_found",
            "video_id": video_id,
            "message": f"No plan found for video_id '{video_id}'. Use plan_video first.",
        }

    return {
        "status": "ok",
        "video_id": video_id,
        "title": plan.get("title", ""),
        "total_scenes": plan.get("total_scenes", 0),
        "mood": plan.get("mood", ""),
        "message": "Plan exists. Pipeline execution is available via the WebSocket endpoint.",
    }


def list_video_categories() -> dict:
    """Return the video types CutTo can produce.

    Returns:
        A dict with a list of supported video categories, each including
        id, name, description, and an example prompt.
    """
    return {
        "status": "ok",
        "categories": VIDEO_CATEGORIES,
        "total": len(VIDEO_CATEGORIES),
        "message": "Use any of these categories with plan_video to create a scene plan.",
    }


# ---------------------------------------------------------------------------
# ADK Agent definition
# ---------------------------------------------------------------------------

try:
    from google.adk.agents import Agent

    root_agent = Agent(
        name="cutto_director",
        model="gemini-2.0-flash",
        description=(
            "AI video director that creates professional short videos "
            "from text descriptions. Supports stories, explainers, "
            "documentaries, tutorials, marketing videos, and motivational pieces."
        ),
        instruction=SYSTEM_PROMPT,
        tools=[plan_video, get_pipeline_status, list_video_categories],
    )

except ImportError:
    # google-adk is not installed — create a lightweight stub so imports
    # don't crash and tests can still verify the module structure.

    class _StubAgent:
        """Minimal stand-in when google.adk is not installed."""

        def __init__(self, *, name: str, model: str, description: str,
                     instruction: str, tools: list):
            self.name = name
            self.model = model
            self.description = description
            self.instruction = instruction
            self.tools = tools

        def __repr__(self) -> str:
            return (
                f"StubAgent(name={self.name!r}, tools={[t.__name__ for t in self.tools]})"
            )

    logger.warning(
        "google-adk is not installed. Using a stub Agent. "
        "Install with: pip install google-adk"
    )

    root_agent = _StubAgent(
        name="cutto_director",
        model="gemini-2.0-flash",
        description=(
            "AI video director that creates professional short videos "
            "from text descriptions. Supports stories, explainers, "
            "documentaries, tutorials, marketing videos, and motivational pieces."
        ),
        instruction=SYSTEM_PROMPT,
        tools=[plan_video, get_pipeline_status, list_video_categories],
    )
