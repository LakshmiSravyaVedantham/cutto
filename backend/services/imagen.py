from google import genai
from pathlib import Path
import logging
from backend.config import GOOGLE_API_KEY, IMAGEN_MODEL

logger = logging.getLogger(__name__)

client = genai.Client(api_key=GOOGLE_API_KEY)

def generate_image(prompt: str, output_path: str) -> str:
    """Generate an image from a text prompt using Imagen API."""
    logger.info(f"Generating image: {prompt[:80]}...")
    response = client.models.generate_images(
        model=IMAGEN_MODEL,
        prompt=prompt,
        config={"number_of_images": 1}
    )
    if not response.generated_images:
        raise RuntimeError("Imagen returned no images")
    image_data = response.generated_images[0].image.image_bytes
    Path(output_path).write_bytes(image_data)
    logger.info(f"Image saved: {output_path} ({len(image_data)} bytes)")
    return output_path
