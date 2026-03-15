import logging
from pathlib import Path

from backend.client import get_client
from backend.config import IMAGEN_MODEL

logger = logging.getLogger(__name__)


CONSISTENCY_SUFFIX = (
    " Shot on ARRI Alexa, cinematic shallow depth of field f/1.4."
    " Professional film lighting, rich color grading, fine organic grain."
    " Photorealistic, production-quality frame from a feature film."
    " Maintain exact same visual style, color palette, character design,"
    " and lighting setup across all frames for visual consistency."
)


def generate_image(prompt: str, output_path: str) -> str:
    """Generate an image from a text prompt using Imagen API."""
    full_prompt = prompt + CONSISTENCY_SUFFIX
    logger.info(f"Generating image: {full_prompt[:100]}...")
    response = get_client().models.generate_images(
        model=IMAGEN_MODEL, prompt=full_prompt, config={"number_of_images": 1}
    )
    if not response.generated_images:
        raise RuntimeError("Imagen returned no images")
    image_data = response.generated_images[0].image.image_bytes
    Path(output_path).write_bytes(image_data)
    logger.info(f"Image saved: {output_path} ({len(image_data)} bytes)")
    return output_path
