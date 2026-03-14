"""Veo video generation service — produces animated video clips from text prompts."""

import logging
import time
import urllib.request
from pathlib import Path

from backend.config import GOOGLE_API_KEY, VEO_MODEL

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    global _client
    if _client is None:
        from google import genai

        _client = genai.Client(api_key=GOOGLE_API_KEY)
    return _client


STYLE_SUFFIX = (
    " Cinematic quality, photorealistic, real-world footage style."
    " Natural lighting, shallow depth of field, vivid colors."
    " Smooth professional camera movement."
)


def generate_video(
    prompt: str, output_path: str, duration_seconds: int = 5, seed: int | None = None
) -> str:
    """Generate an animated video clip from a text prompt using Veo.

    Polls the long-running operation until completion (up to 5 minutes).
    Returns the output_path on success.
    """
    full_prompt = prompt + STYLE_SUFFIX
    capped_duration = min(duration_seconds, 8)
    logger.info(
        f"[Veo] Starting video generation (duration={capped_duration}s, model={VEO_MODEL})"
    )
    logger.info(f"[Veo] Prompt: {full_prompt[:200]}...")
    logger.info(f"[Veo] Output path: {output_path}")

    config = {
        "number_of_videos": 1,
        "duration_seconds": capped_duration,
    }
    if seed is not None:
        logger.info(
            "[Veo] Ignoring seed=%s because the current Gemini Veo API does not accept it",
            seed,
        )

    t0 = time.time()
    client = _get_client()
    operation = client.models.generate_videos(
        model=VEO_MODEL,
        prompt=full_prompt,
        config=config,
    )
    logger.info(
        f"[Veo] Operation submitted in {time.time() - t0:.1f}s, polling for completion..."
    )

    # Poll until done — timeout after 5 minutes
    max_wait = 300
    poll_interval = 10
    elapsed = 0

    while not operation.done and elapsed < max_wait:
        time.sleep(poll_interval)
        elapsed += poll_interval
        try:
            operation = _get_client().operations.get(operation)
            logger.debug(f"[Veo] Poll at {elapsed}s — done={operation.done}")
        except Exception as e:
            logger.warning(f"[Veo] Poll error at {elapsed}s: {e}")
        if elapsed % 30 == 0:
            logger.info(f"[Veo] Still generating... ({elapsed}s / {max_wait}s max)")

    total_time = time.time() - t0
    logger.info(
        f"[Veo] Polling finished — done={operation.done}, total_time={total_time:.1f}s"
    )

    if not operation.done:
        raise RuntimeError(f"Veo timed out after {max_wait}s")

    if operation.error:
        logger.error(f"[Veo] Operation returned error: {operation.error}")
        raise RuntimeError(f"Veo error: {operation.error}")

    result = operation.result
    if not result or not result.generated_videos:
        logger.error(f"[Veo] No videos in result. result={result}")
        raise RuntimeError("Veo returned no videos")

    video = result.generated_videos[0]
    video_obj = video.video

    # Veo returns a download URI, not inline bytes
    video_bytes = video_obj.video_bytes
    if video_bytes:
        logger.info(f"[Veo] Got inline bytes: {len(video_bytes):,} bytes")
        Path(output_path).write_bytes(video_bytes)
    elif hasattr(video_obj, "uri") and video_obj.uri:
        uri = video_obj.uri
        logger.info(f"[Veo] Downloading video from URI: {uri[:100]}...")
        # Use header-based auth to avoid key in logs/URLs
        if "?" in uri:
            download_url = f"{uri}&key={GOOGLE_API_KEY}"
        else:
            download_url = f"{uri}?key={GOOGLE_API_KEY}"
        req = urllib.request.Request(download_url)
        with urllib.request.urlopen(req, timeout=120) as resp:
            video_bytes = resp.read()
        if not video_bytes:
            raise RuntimeError("Veo URI returned empty response")
        Path(output_path).write_bytes(video_bytes)
        logger.info(f"[Veo] Downloaded and saved: {len(video_bytes):,} bytes")
    else:
        logger.error(f"[Veo] No video bytes or URI. video_obj={video_obj}")
        raise RuntimeError("Veo returned no video data")

    logger.info(
        f"[Veo] Video saved: {output_path} ({len(video_bytes):,} bytes, {total_time:.1f}s total)"
    )
    return output_path
