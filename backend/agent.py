from google import genai
from google.genai import types
from backend.models import ScenePlan
from backend.config import GOOGLE_API_KEY, GEMINI_MODEL, GEMINI_IMAGE_MODEL
import json
import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are CutTo, a world-class AI video director and scriptwriter. You create compelling, professional-quality video scripts with visually consistent scenes.

PHASE 1 - CONVERSATION:
Ask the user what video they want to make. Clarify in 3-4 quick questions max:
- Topic and key message
- Duration (suggest 30-60 seconds for short, 1-2 minutes for detailed)
- Tone (dramatic, upbeat, calm, inspiring, playful)
- Audience (general, kids, professionals, social media)

Be conversational and brief.

PHASE 2 - PLANNING:
When you have enough info, generate a scene-by-scene plan.

CRITICAL — VISUAL CONSISTENCY:
Before writing scenes, define a "visual_style_anchor" in the JSON. This is a detailed description of the art style, color palette, lighting, and any recurring characters or objects. EVERY scene's visual_prompt MUST begin with this exact anchor text, followed by the scene-specific details. This ensures all scenes look like they belong to the same video.

Example anchor: "Digital illustration, soft watercolor style, warm golden lighting, muted earth tones. A young woman with short black hair, round glasses, wearing a blue cardigan and white t-shirt"

Then every visual_prompt starts with that anchor: "[anchor text]. She stands in a library reaching for a book on a high shelf."

CRITICAL — SCRIPT QUALITY:
- Write narration like a professional documentary or explainer script
- Each sentence should be clear, punchy, and convey exactly one idea
- Use active voice, concrete language, and vivid verbs
- Build a narrative arc: hook the viewer in scene 1, build understanding, end with impact
- Avoid filler words, cliches, and vague statements
- Read each narration aloud mentally — it must sound natural when spoken

Output the scene plan as a JSON code block with this exact format:
```json
{
  "title": "Video Title",
  "total_scenes": N,
  "mood": "one of: dramatic, upbeat, calm, inspiring, playful",
  "visual_style_anchor": "Detailed description of art style, color palette, lighting, and any recurring characters/objects that appears in every scene",
  "scenes": [
    {
      "scene_number": 1,
      "narration": "Professional voiceover script for this scene",
      "visual_prompt": "[visual_style_anchor]. Scene-specific details here",
      "visual_type": "image",
      "target_duration": 5
    }
  ]
}
```

PHASE 3 - APPROVAL:
After presenting the plan, ask the user if they want to change anything.
If they approve, respond with exactly: "APPROVED: Starting video generation now!"

Rules:
- Keep total video under 2 minutes
- Maximum 8 scenes
- Each narration should be 1-3 sentences
- EVERY visual_prompt MUST start with the visual_style_anchor word-for-word
- Mood must be one of: dramatic, upbeat, calm, inspiring, playful
"""


class ConversationSession:
    """Manages a conversation with Gemini for video planning."""

    def __init__(self):
        self.history: list[dict] = []
        self.client = genai.Client(api_key=GOOGLE_API_KEY)
        self.scene_plan: ScenePlan | None = None

    async def send_message(
        self, message: str
    ) -> tuple[str, bytes | None, ScenePlan | None, bool]:
        """Send message to Gemini.

        Returns: (text_response, image_bytes_or_none, scene_plan_or_none, pipeline_approved)
        """
        self.history.append({"role": "user", "parts": [{"text": message}]})

        try:
            response = self.client.models.generate_content(
                model=GEMINI_IMAGE_MODEL,
                contents=self.history,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_modalities=["TEXT", "IMAGE"],
                ),
            )
        except Exception as e:
            logger.error(f"Gemini image model failed: {e}, falling back to text-only")
            response = self.client.models.generate_content(
                model=GEMINI_MODEL,
                contents=self.history,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                ),
            )

        text_parts = []
        image_bytes = None

        for part in response.candidates[0].content.parts:
            if hasattr(part, "text") and part.text:
                text_parts.append(part.text)
            elif hasattr(part, "inline_data") and part.inline_data:
                image_bytes = part.inline_data.data

        full_text = "\n".join(text_parts)
        self.history.append({"role": "model", "parts": [{"text": full_text}]})

        # Try to extract scene plan from response
        scene_plan = extract_scene_plan(full_text)
        if scene_plan:
            self.scene_plan = scene_plan

        # Check if approved
        approved = is_approved(full_text)

        return full_text, image_bytes, scene_plan, approved


def extract_scene_plan(text: str) -> ScenePlan | None:
    """Extract JSON scene plan from Gemini's response text."""
    try:
        start = text.index("```json") + 7
        end = text.index("```", start)
        json_str = text[start:end].strip()
        data = json.loads(json_str)
        return ScenePlan(**data)
    except (ValueError, json.JSONDecodeError, Exception) as e:
        logger.debug(f"No scene plan found in response: {e}")
        return None


def is_approved(text: str) -> bool:
    """Check if the response indicates user approval."""
    return "APPROVED:" in text.upper()
