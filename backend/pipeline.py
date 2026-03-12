import asyncio
import subprocess
import tempfile
import logging
from pathlib import Path
from typing import Callable, Optional

from backend.models import ScenePlan, Scene, PipelineProgress
from backend.services import imagen, tts, ffmpeg
from backend.config import MUSIC_DIR, GOOGLE_API_KEY, GEMINI_IMAGE_MODEL

logger = logging.getLogger(__name__)

MUSIC_MAP = {
    "dramatic": "dramatic.mp3",
    "upbeat": "upbeat.mp3",
    "calm": "calm.mp3",
    "inspiring": "inspiring.mp3",
    "playful": "playful.mp3",
}


async def run_pipeline(
    plan: ScenePlan,
    progress_callback: Optional[Callable] = None,
) -> str:
    """Run the full video generation pipeline."""
    work_dir = Path(tempfile.mkdtemp(prefix="cutto_"))
    scene_clips = []

    for scene in plan.scenes:
        if progress_callback:
            await progress_callback(
                PipelineProgress(
                    video_id=plan.video_id,
                    scene=scene.scene_number,
                    step="visual",
                    status="in_progress",
                )
            )

        clip_path = await process_scene(scene, work_dir, style_anchor=plan.visual_style_anchor)
        scene_clips.append(clip_path)

        if progress_callback:
            await progress_callback(
                PipelineProgress(
                    video_id=plan.video_id,
                    scene=scene.scene_number,
                    step="clip",
                    status="done",
                )
            )

    if progress_callback:
        await progress_callback(
            PipelineProgress(
                video_id=plan.video_id,
                scene=0,
                step="assembly",
                status="in_progress",
            )
        )

    final_path = await assemble_final(plan, scene_clips, work_dir)

    if progress_callback:
        await progress_callback(
            PipelineProgress(
                video_id=plan.video_id,
                scene=0,
                step="complete",
                status="done",
            )
        )

    return final_path


async def generate_image_with_fallback(prompt: str, output_path: str) -> str:
    """Try Imagen first, fall back to Gemini native image generation."""
    try:
        return await asyncio.to_thread(imagen.generate_image, prompt, output_path)
    except Exception as e:
        logger.warning(f"Imagen failed ({e}), retrying once...")
        try:
            return await asyncio.to_thread(imagen.generate_image, prompt, output_path)
        except Exception as e2:
            logger.warning(
                f"Imagen retry failed ({e2}), falling back to Gemini native image"
            )
            return await asyncio.to_thread(
                gemini_fallback_image, prompt, output_path
            )


def gemini_fallback_image(prompt: str, output_path: str) -> str:
    """Generate image using Gemini's native interleaved output as fallback."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=GOOGLE_API_KEY)
    response = client.models.generate_content(
        model=GEMINI_IMAGE_MODEL,
        contents=f"Generate an image: {prompt}",
        config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
    )
    for part in response.candidates[0].content.parts:
        if hasattr(part, "inline_data") and part.inline_data:
            Path(output_path).write_bytes(part.inline_data.data)
            return output_path
    raise RuntimeError("Gemini fallback produced no image")


async def process_scene(scene: Scene, work_dir: Path, style_anchor: str = "") -> str:
    """Process a single scene: generate image, voiceover, combine."""
    scene_dir = work_dir / f"scene_{scene.scene_number}"
    scene_dir.mkdir(exist_ok=True)

    # Step 1: Build the full visual prompt with style anchor for consistency
    visual_prompt = scene.visual_prompt
    if style_anchor and not visual_prompt.startswith(style_anchor[:50]):
        # Prepend anchor if not already present
        visual_prompt = f"{style_anchor}. {visual_prompt}"

    image_path = str(scene_dir / "visual.png")
    await generate_image_with_fallback(visual_prompt, image_path)

    # Step 2: Generate voiceover FIRST (to get actual duration)
    audio_path = str(scene_dir / "narration.mp3")
    try:
        await tts.synthesize_to_file(scene.narration, audio_path)
    except Exception:
        logger.warning("TTS failed, retrying...")
        await tts.synthesize_to_file(scene.narration, audio_path)

    # Step 3: Get audio duration, use it for Ken Burns
    duration = await asyncio.to_thread(ffmpeg.get_audio_duration, audio_path)
    duration = max(int(duration) + 1, scene.target_duration)

    # Step 4: Apply Ken Burns with actual audio duration
    visual_path = str(scene_dir / "visual.mp4")
    await asyncio.to_thread(
        ffmpeg.create_ken_burns, image_path, visual_path, duration
    )

    # Step 5: Combine visual + audio into scene clip
    clip_path = str(scene_dir / "clip.mp4")
    await asyncio.to_thread(
        ffmpeg.create_scene_clip, visual_path, audio_path, clip_path
    )

    return clip_path


async def assemble_final(
    plan: ScenePlan, scene_clips: list[str], work_dir: Path
) -> str:
    """Concatenate scene clips, add music, produce final video."""
    if len(scene_clips) == 1:
        concat_path = scene_clips[0]
    else:
        concat_path = str(work_dir / "concat.mp4")
        await asyncio.to_thread(ffmpeg.concat_clips, scene_clips, concat_path)

    # Add background music
    music_file = MUSIC_MAP.get(plan.mood, "calm.mp3")
    music_path = str(Path(MUSIC_DIR) / music_file)
    final_path = str(work_dir / "final.mp4")

    if Path(music_path).exists():
        await asyncio.to_thread(
            ffmpeg.add_music, concat_path, music_path, final_path
        )
    else:
        logger.warning(f"Music file not found: {music_path}, skipping music")
        final_path = concat_path

    return final_path
