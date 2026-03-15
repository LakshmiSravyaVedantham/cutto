import asyncio
import base64
import logging
import tempfile
from pathlib import Path
from typing import Callable, Optional

from backend.client import get_client
from backend.config import (
    GEMINI_IMAGE_MODEL,
    GEMINI_MODEL,
    MUSIC_DIR,
    PIPELINE_PARALLEL_BATCH_SIZE,
    SCENE_TIMEOUT_SECONDS,
)
from backend.models import PipelineProgress, Scene, ScenePlan
from backend.services import ffmpeg, imagen, lipsync, tts, veo

logger = logging.getLogger(__name__)

MUSIC_MAP = {
    "dramatic": "dramatic.mp3",
    "upbeat": "upbeat.mp3",
    "calm": "calm.mp3",
    "inspiring": "inspiring.mp3",
    "playful": "playful.mp3",
}


PARALLEL_BATCH_SIZE = max(1, PIPELINE_PARALLEL_BATCH_SIZE)
SCENE_TIMEOUT = max(60, SCENE_TIMEOUT_SECONDS)


async def run_pipeline(
    plan: ScenePlan,
    progress_callback: Optional[Callable] = None,
) -> str:
    """Run the full video generation pipeline with parallel scene processing."""
    work_dir = Path(tempfile.mkdtemp(prefix="cutto_"))

    # Process scenes in parallel batches for speed
    scene_clips: list[str | None] = [None] * len(plan.scenes)

    failed_scenes = 0
    fail_lock = asyncio.Lock()

    async def process_with_progress(scene: Scene, index: int) -> None:
        nonlocal failed_scenes
        if progress_callback:
            await progress_callback(
                PipelineProgress(
                    video_id=plan.video_id,
                    scene=scene.scene_number,
                    step="visual",
                    status="in_progress",
                )
            )

        try:
            clip_path = await asyncio.wait_for(
                process_scene(
                    scene,
                    work_dir,
                    style_anchor=plan.visual_style_anchor,
                    audio_driven=plan.audio_driven,
                    mood=plan.mood,
                ),
                timeout=SCENE_TIMEOUT,
            )
            scene_clips[index] = clip_path
        except (asyncio.TimeoutError, Exception) as e:
            async with fail_lock:
                failed_scenes += 1
                current_failures = failed_scenes
            logger.error(f"Scene {scene.scene_number} failed: {e}")
            if progress_callback:
                await progress_callback(
                    PipelineProgress(
                        video_id=plan.video_id,
                        scene=scene.scene_number,
                        step="clip",
                        status="error",
                        message=str(e)[:200],
                    )
                )
            if current_failures >= 3:
                raise RuntimeError("Too many scene failures (3+), aborting pipeline")
            return

        # Extract thumbnail for frontend preview
        thumb_b64 = ""
        if clip_path:
            thumb_path = str(Path(clip_path).parent / "thumb.jpg")
            try:
                await asyncio.to_thread(ffmpeg.extract_thumbnail, clip_path, thumb_path)
                thumb_b64 = base64.b64encode(Path(thumb_path).read_bytes()).decode()
            except Exception:
                logger.warning(
                    f"Thumbnail extraction failed for scene {scene.scene_number}"
                )

        if progress_callback:
            await progress_callback(
                PipelineProgress(
                    video_id=plan.video_id,
                    scene=scene.scene_number,
                    step="clip",
                    status="done",
                    thumbnail=thumb_b64,
                )
            )

    # Run in batches of PARALLEL_BATCH_SIZE with staggered starts
    # to avoid overwhelming Veo's per-minute rate limit
    VEO_STAGGER_SECONDS = 10

    async def staggered_process(scene: Scene, index: int, delay: float) -> None:
        if delay > 0:
            await asyncio.sleep(delay)
        await process_with_progress(scene, index)

    for batch_start in range(0, len(plan.scenes), PARALLEL_BATCH_SIZE):
        batch = plan.scenes[batch_start : batch_start + PARALLEL_BATCH_SIZE]
        tasks = [
            staggered_process(scene, batch_start + i, i * VEO_STAGGER_SECONDS)
            for i, scene in enumerate(batch)
        ]
        logger.info(
            f"Processing scenes {batch_start + 1}-{batch_start + len(batch)} "
            f"(staggered {VEO_STAGGER_SECONDS}s apart)"
        )
        await asyncio.gather(*tasks)

    if progress_callback:
        await progress_callback(
            PipelineProgress(
                video_id=plan.video_id,
                scene=0,
                step="assembly",
                status="in_progress",
            )
        )

    valid_clips = [c for c in scene_clips if c]
    if not valid_clips:
        raise RuntimeError("All scenes failed — no clips to assemble")
    final_path = await assemble_final(plan, valid_clips, work_dir)

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


async def generate_video_with_fallback(
    prompt: str, output_path: str, duration: int = 8
) -> tuple[str, bool]:
    """Try Veo video generation first, fall back to Imagen static image.

    Returns (output_path, is_video) — is_video=True means animated clip, False means static image.
    """
    # Try Veo for animated video (with rate limit retry)
    for attempt in range(2):
        try:
            if attempt > 0:
                logger.info("Veo retry after rate limit — waiting 15s...")
                await asyncio.sleep(15)
            logger.info("Attempting Veo video generation...")
            result = await asyncio.to_thread(
                veo.generate_video, prompt, output_path, duration
            )
            logger.info("Veo succeeded — animated video generated")
            return result, True
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                if attempt == 0:
                    logger.warning("Veo rate limited, will retry after delay...")
                    continue
            logger.warning(f"Veo failed ({e}), falling back to Imagen static image")
            break

    # Fall back to Imagen static image
    image_path = output_path.replace(".mp4", ".png")
    try:
        await asyncio.to_thread(imagen.generate_image, prompt, image_path)
        return image_path, False
    except Exception as e2:
        logger.warning(f"Imagen failed ({e2}), retrying Imagen once...")
        try:
            await asyncio.to_thread(imagen.generate_image, prompt, image_path)
            return image_path, False
        except Exception as e3:
            logger.warning(f"Imagen retry failed ({e3}), trying Gemini native fallback")
            try:
                await asyncio.to_thread(gemini_fallback_image, prompt, image_path)
                return image_path, False
            except Exception as e4:
                raise RuntimeError(
                    f"All image generation failed (Veo, Imagen x2, Gemini): {e4}"
                ) from e4


def gemini_fallback_image(prompt: str, output_path: str) -> str:
    """Generate image using Gemini's native interleaved output as fallback."""
    from google.genai import types

    client = get_client()
    response = client.models.generate_content(
        model=GEMINI_IMAGE_MODEL,
        contents=f"Generate an image: {prompt}",
        config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
    )
    if not response.candidates or not response.candidates[0].content.parts:
        raise RuntimeError("Gemini fallback returned empty response")
    for part in response.candidates[0].content.parts:
        if hasattr(part, "inline_data") and part.inline_data:
            Path(output_path).write_bytes(part.inline_data.data)
            return output_path
    raise RuntimeError("Gemini fallback produced no image")


def enhance_visual_prompt(prompt: str, mood: str = "") -> str:
    """Use Gemini to decompose and rebuild a visual prompt into cinema-grade shot description.

    Uses a structured decomposition technique (inspired by nano-banana/flow-style prompt engineering):
    1. Extract the SUBJECT (who/what is in frame)
    2. Define the ACTION (what is moving, how)
    3. Set the CAMERA (rig, lens, movement)
    4. Design the LIGHTING (setup, color temp, quality)
    5. Choose the PALETTE (color grade, mood)
    6. Add TEXTURE (grain, haze, bokeh, atmosphere)
    Then merge all elements into one cohesive shot description.
    """
    try:
        from google.genai import types

        client = get_client()
        enhance_instruction = (
            "You are a world-class Director of Photography and prompt engineer. "
            "You use the FLOW decomposition method to craft perfect video generation prompts.\n\n"
            "STEP 1 — DECOMPOSE the input into these 6 elements (think silently, don't output this):\n"
            "  SUBJECT: Who/what is the main focus? (person, object, landscape)\n"
            "  ACTION: What continuous motion is happening? (speaking, walking, flowing, rotating)\n"
            "  CAMERA: What rig, lens, and movement? (Steadicam 85mm f/1.4, slow push-in)\n"
            "  LIGHTING: What setup and color temp? (Rembrandt side-light 3200K, golden hour backlight)\n"
            "  PALETTE: What color grade? (teal-amber, desaturated earth, warm golden)\n"
            "  TEXTURE: What atmosphere? (film grain, bokeh, haze, dust particles, lens flare)\n\n"
            "STEP 2 — RECONSTRUCT into a single vivid paragraph (80-120 words) merging all 6 elements "
            "into one cohesive shot description. Write it as a professional shot brief.\n\n"
            "FLOW EXAMPLES:\n\n"
            "Input: A teacher explaining photosynthesis\n"
            "Decompose: SUBJECT=young female teacher | ACTION=speaking to camera, gesturing with hands | "
            "CAMERA=Steadicam MCU, 85mm f/1.4, slow push-in | LIGHTING=soft three-point, 4000K key | "
            "PALETTE=warm amber and green | TEXTURE=creamy bokeh, subtle film grain\n"
            "Output: Steadicam medium close-up on 85mm lens at f/1.4, slowly pushing in. A warm, "
            "enthusiastic young female teacher speaks directly to camera, her mouth moving clearly with "
            "each word, hands gesturing expressively as she explains. Soft three-point lighting at 4000K "
            "wraps her face with a natural glow. Behind her, a sunlit classroom dissolves into creamy "
            "circular bokeh — green plants and amber wood tones blurred beautifully. Fine organic film "
            "grain adds texture. Warm amber and leaf-green color palette throughout.\n\n"
            "Input: The inside of a volcano\n"
            "Decompose: SUBJECT=magma chamber interior | ACTION=lava bubbling, rocks cracking, heat shimmer | "
            "CAMERA=drone descending, 24mm wide, slow crane down | LIGHTING=molten orange glow from below, "
            "rim light on rock edges | PALETTE=deep crimson, molten orange, volcanic black | "
            "TEXTURE=heat distortion, embers floating, smoke wisps\n"
            "Output: Drone shot on 24mm wide lens descending into a massive volcanic chamber. Molten "
            "lava bubbles and churns below, casting a fierce orange glow upward that rim-lights jagged "
            "obsidian rock formations. Heat shimmer distorts the air as glowing embers drift upward like "
            "fireflies. Cracks spider across cooling rock surfaces, revealing veins of molten magma beneath. "
            "Thick smoke wisps curl through shafts of amber light. Deep crimson and molten orange color "
            "palette against volcanic black. BBC Earth documentary quality, macro detail on lava textures.\n\n"
            "HARD RULES:\n"
            "- ONLY photorealistic real-world footage — NEVER cartoon, anime, illustration, CGI\n"
            "- SPEAKER scenes MUST show real human face front-facing, mouth clearly moving, eyes engaged\n"
            "- Every prompt MUST have continuous physical motion — NEVER a still photograph\n"
            "- NEVER use quotation marks in output\n"
            "- Do NOT add dialogue, narration, or sound descriptions\n"
            f"- Mood: {mood or 'cinematic'}\n"
            "Output ONLY the final reconstructed prompt paragraph, nothing else."
        )
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[{"role": "user", "parts": [{"text": f"FLOW decompose and reconstruct: {prompt}"}]}],
            config=types.GenerateContentConfig(
                system_instruction=enhance_instruction,
            ),
        )
        if response.candidates and response.candidates[0].content.parts:
            enhanced = response.candidates[0].content.parts[0].text.strip()
            if len(enhanced) > 20:
                logger.info(f"[Enhance] {prompt[:60]}... -> {enhanced[:80]}...")
                return enhanced
    except Exception as e:
        logger.warning(f"Prompt enhancement failed ({e}), using original")
    return prompt


async def process_scene(
    scene: Scene,
    work_dir: Path,
    style_anchor: str = "",
    audio_driven: bool = False,
    mood: str = "",
) -> str:
    """Process a single scene: generate video/image, voiceover, combine.

    Default (audio_driven=False): video is king — audio adjusts to fit video duration.
    audio_driven=True: audio is king — video adjusts to fit audio duration.
    """
    scene_dir = work_dir / f"scene_{scene.scene_number}"
    scene_dir.mkdir(exist_ok=True)

    # Step 1: Build the full visual prompt with style anchor
    visual_prompt = scene.visual_prompt
    if style_anchor and not visual_prompt.startswith(style_anchor[:50]):
        visual_prompt = f"{style_anchor}. {visual_prompt}"

    # Step 1b: AI-enhance the prompt for better cinematography
    visual_prompt = await asyncio.to_thread(enhance_visual_prompt, visual_prompt, mood)

    # Strip quotation marks — Veo best practices say avoid quotes in prompts
    visual_prompt = visual_prompt.replace('"', "").replace("'", "")

    # Step 2: Generate voiceover with speaker-specific voice (parallel with visual)
    raw_audio = str(scene_dir / "narration_raw.mp3")
    tts_task = asyncio.create_task(
        generate_tts(scene.narration, raw_audio, scene.speaker)
    )

    # Step 3: Generate visual (video via Veo, or fallback to Imagen)
    visual_output = str(scene_dir / "visual.mp4")
    visual_path, is_video = await generate_video_with_fallback(
        visual_prompt, visual_output, duration=scene.target_duration
    )

    # Step 4: Wait for TTS, then decide who drives duration
    await tts_task
    audio_dur = await asyncio.to_thread(ffmpeg.get_audio_duration, raw_audio)
    audio_path = str(scene_dir / "narration.mp3")

    if audio_driven:
        # AUDIO-DRIVEN: audio stays as-is, video stretches/trims to match
        duration = max(int(audio_dur) + 1, scene.target_duration)
        Path(audio_path).write_bytes(Path(raw_audio).read_bytes())
        logger.info(f"Scene {scene.scene_number}: audio-driven, dur={duration}s")
    else:
        # VIDEO-DRIVEN (default): video stays natural, audio speeds up/pads to fit
        if is_video:
            vid_dur = await asyncio.to_thread(ffmpeg.get_video_duration, visual_path)
            duration = max(int(vid_dur), scene.target_duration)
        else:
            duration = scene.target_duration
        await asyncio.to_thread(
            ffmpeg.adjust_audio_duration, raw_audio, audio_path, float(duration)
        )
        logger.info(
            f"Scene {scene.scene_number}: video-driven, audio {audio_dur:.1f}s -> {duration}s"
        )

    # Step 5: Adjust visual to final duration
    if not is_video:
        ken_burns_path = str(scene_dir / "visual_kb.mp4")
        await asyncio.to_thread(
            ffmpeg.create_ken_burns, visual_path, ken_burns_path, duration
        )
        visual_path = ken_burns_path
    elif audio_driven:
        # Only stretch/trim video in audio-driven mode
        adjusted_path = str(scene_dir / "visual_adjusted.mp4")
        await asyncio.to_thread(
            ffmpeg.adjust_video_duration, visual_path, adjusted_path, duration
        )
        visual_path = adjusted_path

    # Step 6: Lipsync only for character dialogue scenes (not narrator)
    is_character = scene.speaker.startswith("character_")
    if is_character:
        if is_video and lipsync.is_available():
            logger.info(
                f"[Lipsync] Applying for {scene.speaker} (scene {scene.scene_number})"
            )
            synced_path = str(scene_dir / "visual_synced.mp4")
            synced = await asyncio.to_thread(
                lipsync.apply_lipsync, visual_path, audio_path, synced_path
            )
            if synced != visual_path:
                visual_path = synced
                logger.info(f"[Lipsync] Success — synced video at {synced}")
            else:
                logger.warning(
                    f"[Lipsync] Failed or no face detected (scene {scene.scene_number}), "
                    "using original video — character may not have clear front-facing face"
                )
        elif not is_video:
            logger.info(
                f"[Lipsync] Skipped — static image, no face (scene {scene.scene_number})"
            )
        elif not lipsync.is_available():
            logger.warning(
                f"[Lipsync] Skipped — Wav2Lip not available (scene {scene.scene_number})"
            )
    else:
        logger.info(f"[Lipsync] Skipped — narrator scene (scene {scene.scene_number})")

    # Step 7: Combine visual + audio into scene clip
    clip_path = str(scene_dir / "clip.mp4")
    await asyncio.to_thread(
        ffmpeg.create_scene_clip, visual_path, audio_path, clip_path
    )

    return clip_path


async def generate_tts(text: str, audio_path: str, speaker: str = "narrator"):
    """Generate TTS with speaker-specific voice and one retry."""
    voice = tts.get_voice_for_speaker(speaker)
    try:
        await tts.synthesize_to_file(text, audio_path, voice=voice, speaker=speaker)
    except Exception:
        logger.warning("TTS failed, retrying...")
        await tts.synthesize_to_file(text, audio_path, voice=voice, speaker=speaker)


async def assemble_final(
    plan: ScenePlan, scene_clips: list[str], work_dir: Path
) -> str:
    """Concatenate scene clips, add music, produce final video."""
    if len(scene_clips) == 1:
        concat_path = scene_clips[0]
    else:
        concat_path = str(work_dir / "concat.mp4")
        # Use crossfade transitions for professional look
        await asyncio.to_thread(
            ffmpeg.crossfade_concat_clips, scene_clips, concat_path, 0.5
        )

    # Skip music — clean video with voiceover only
    final_path = concat_path
    logger.info("[Music] Skipped — clean voiceover mode")

    return final_path
