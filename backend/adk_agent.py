"""
CutTo ADK Agent — Multi-agent architecture using Google Agent Development Kit.

Three specialized agents work together:
  1. director_agent  — Creative conversation, interprets user intent
  2. storyboard_agent — Generates structured scene plans with visual prompts
  3. root_agent (orchestrator) — Routes between director and storyboard

Usage:
    from backend.adk_agent import root_agent

The existing agent.py and main.py are NOT modified — this is additive.
"""

import logging

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

        from backend.config import GEMINI_MODEL, GOOGLE_API_KEY

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


def revise_scene(video_id: str, scene_number: int, revision_note: str) -> dict:
    """Revise a specific scene in an existing plan based on user feedback.

    Args:
        video_id: The UUID of the video plan to revise.
        scene_number: The scene number to revise (1-indexed).
        revision_note: Natural language description of what to change.
                      Example: "Make this scene more dramatic with stormy weather"

    Returns:
        A dict with the updated scene details and status.
    """
    plan = _active_plans.get(video_id)
    if not plan:
        return {
            "status": "not_found",
            "message": f"No plan found for video_id '{video_id}'.",
        }

    scenes = plan.get("scenes", [])
    target = None
    for s in scenes:
        if s.get("scene_number") == scene_number:
            target = s
            break

    if not target:
        return {
            "status": "error",
            "message": f"Scene {scene_number} not found in plan (has {len(scenes)} scenes).",
        }

    try:
        from google import genai
        from google.genai import types

        from backend.config import GEMINI_MODEL, GOOGLE_API_KEY

        client = genai.Client(api_key=GOOGLE_API_KEY)

        revision_prompt = (
            f"Revise scene {scene_number} of this video plan.\n\n"
            f"Current scene:\n"
            f"- Speaker: {target.get('speaker')}\n"
            f"- Narration: {target.get('narration')}\n"
            f"- Visual: {target.get('visual_prompt')}\n\n"
            f"User's revision request: {revision_note}\n\n"
            f"Visual style anchor (MUST be preserved): {plan.get('visual_style_anchor', '')}\n\n"
            "Output ONLY the revised scene as a JSON object with keys: "
            "scene_number, speaker, narration, visual_prompt, visual_type, target_duration."
        )

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[{"role": "user", "parts": [{"text": revision_prompt}]}],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
            ),
        )

        if response.candidates and response.candidates[0].content.parts:
            import json

            text = response.candidates[0].content.parts[0].text
            # Try to extract JSON from response
            try:
                start = text.index("{")
                end = text.rindex("}") + 1
                revised = json.loads(text[start:end])
                target.update(revised)
                return {
                    "status": "ok",
                    "scene_number": scene_number,
                    "revised_scene": target,
                    "message": f"Scene {scene_number} revised successfully.",
                }
            except (ValueError, json.JSONDecodeError) as parse_err:
                logger.warning(f"Failed to parse revised scene JSON: {parse_err}")

        return {
            "status": "error",
            "message": "Could not parse the revised scene from Gemini's response.",
        }

    except Exception as e:
        logger.error(f"revise_scene failed: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


# ---------------------------------------------------------------------------
# ADK Agent definition — multi-agent architecture
# ---------------------------------------------------------------------------

# Specialized instruction for the director (conversation) agent
DIRECTOR_INSTRUCTION = """You are the Creative Director of CutTo. Your job is to:
1. Understand what video the user wants to create
2. Ask 2-3 insightful questions about story, audience, and visual style
3. Show creative enthusiasm and suggest bold ideas
4. Once you understand the vision, hand off to the storyboard agent

Speak like a confident film director. Use filmmaking language.
React to ideas with genuine creative excitement.
"""

# Specialized instruction for the storyboard agent
STORYBOARD_INSTRUCTION = """You are the Storyboard Artist of CutTo. Your job is to:
1. Take a video concept and create a detailed 8-scene plan
2. Use the plan_video tool to generate the structured scene plan
3. Present the plan clearly with scene descriptions
4. Use revise_scene to modify individual scenes based on feedback

Follow the scene plan format exactly. Ensure visual consistency across all scenes.
"""

_ALL_TOOLS = [plan_video, get_pipeline_status, list_video_categories, revise_scene]

try:
    from google.adk.agents import Agent

    # Sub-agent: handles creative conversation and vision-setting
    director_agent = Agent(
        name="creative_director",
        model="gemini-2.0-flash",
        description=(
            "Creative director who understands the user's video vision. "
            "Asks insightful questions and shapes the creative direction."
        ),
        instruction=DIRECTOR_INSTRUCTION,
        tools=[list_video_categories],
    )

    # Sub-agent: generates and refines structured scene plans
    storyboard_agent = Agent(
        name="storyboard_artist",
        model="gemini-2.0-flash",
        description=(
            "Storyboard artist who generates detailed scene plans. "
            "Creates 8-scene structured plans and handles revisions."
        ),
        instruction=STORYBOARD_INSTRUCTION,
        tools=[plan_video, revise_scene, get_pipeline_status],
    )

    # Root orchestrator: routes between director and storyboard
    root_agent = Agent(
        name="cutto_director",
        model="gemini-2.0-flash",
        description=(
            "AI video director that creates professional short videos "
            "from text descriptions. Orchestrates creative direction "
            "and storyboard planning through specialized sub-agents."
        ),
        instruction=SYSTEM_PROMPT,
        tools=_ALL_TOOLS,
        sub_agents=[director_agent, storyboard_agent],
    )

except ImportError:

    class _StubAgent:
        """Minimal stand-in when google.adk is not installed."""

        def __init__(
            self,
            *,
            name: str,
            model: str,
            description: str,
            instruction: str,
            tools: list,
            sub_agents: list | None = None,
        ):
            self.name = name
            self.model = model
            self.description = description
            self.instruction = instruction
            self.tools = tools
            self.sub_agents = sub_agents or []

        def __repr__(self) -> str:
            return (
                f"StubAgent(name={self.name!r}, "
                f"tools={[t.__name__ for t in self.tools]}, "
                f"sub_agents={[a.name for a in self.sub_agents]})"
            )

    logger.warning(
        "google-adk is not installed. Using stub Agents. "
        "Install with: pip install google-adk"
    )

    director_agent = _StubAgent(
        name="creative_director",
        model="gemini-2.0-flash",
        description="Creative director sub-agent",
        instruction=DIRECTOR_INSTRUCTION,
        tools=[list_video_categories],
    )

    storyboard_agent = _StubAgent(
        name="storyboard_artist",
        model="gemini-2.0-flash",
        description="Storyboard artist sub-agent",
        instruction=STORYBOARD_INSTRUCTION,
        tools=[plan_video, revise_scene, get_pipeline_status],
    )

    root_agent = _StubAgent(
        name="cutto_director",
        model="gemini-2.0-flash",
        description=(
            "AI video director that creates professional short videos "
            "from text descriptions. Orchestrates creative direction "
            "and storyboard planning through specialized sub-agents."
        ),
        instruction=SYSTEM_PROMPT,
        tools=_ALL_TOOLS,
        sub_agents=[director_agent, storyboard_agent],
    )
