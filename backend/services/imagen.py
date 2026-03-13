import logging
from pathlib import Path

from backend.config import GOOGLE_API_KEY, IMAGEN_MODEL

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    global _client
    if _client is None:
        from google import genai

        _client = genai.Client(api_key=GOOGLE_API_KEY)
    return _client


CONSISTENCY_SUFFIX = " Maintain exact same art style, color palette, character design, and lighting across all frames. Consistent character appearance is critical."


def generate_image(prompt: str, output_path: str) -> str:
    """Generate an image from a text prompt using Imagen API."""
    full_prompt = prompt + CONSISTENCY_SUFFIX
    logger.info(f"Generating image: {full_prompt[:100]}...")
    response = _get_client().models.generate_images(
        model=IMAGEN_MODEL, prompt=full_prompt, config={"number_of_images": 1}
    )
    if not response.generated_images:
        raise RuntimeError("Imagen returned no images")
    image_data = response.generated_images[0].image.image_bytes
    Path(output_path).write_bytes(image_data)
    logger.info(f"Image saved: {output_path} ({len(image_data)} bytes)")
    return output_path
