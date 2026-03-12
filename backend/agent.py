from google import genai
from google.genai import types
from backend.models import ScenePlan
from backend.config import GOOGLE_API_KEY, GEMINI_MODEL, GEMINI_IMAGE_MODEL
import json
import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are CutTo, an AI video director. Your job is to help users create videos from their ideas.

PHASE 1 - CONVERSATION:
Ask the user what video they want to make. Clarify these in 3-4 quick questions max:
- Topic and key message
- Duration (suggest 30-60 seconds for short, 1-2 minutes for detailed)
- Tone (dramatic, upbeat, calm, inspiring, playful)
- Audience (general, kids, professionals, social media)

Be conversational and brief. Don't overwhelm with questions.

PHASE 2 - PLANNING:
When you have enough info, generate a scene-by-scene plan. For each scene, generate a preview image inline showing what that scene will look like.

Output the scene plan as a JSON code block with this exact format:
```json
{
  "title": "Video Title",
  "total_scenes": N,
  "mood": "one of: dramatic, upbeat, calm, inspiring, playful",
  "scenes": [
    {
      "scene_number": 1,
      "narration": "What the voiceover will say for this scene",
      "visual_prompt": "Detailed prompt for image generation",
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
- Visual prompts should be detailed and cinematic
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
