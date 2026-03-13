"""FFmpeg service for CutTo video pipeline.

Provides build_*_cmd functions that return ffmpeg command lists,
wrapper functions that execute them, and ffprobe utilities.
"""

import json
import logging
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


def run_ffmpeg(cmd: list[str]) -> None:
    """Run ffmpeg with -y (overwrite) prefix. Raises RuntimeError on failure."""
    full_cmd = ["ffmpeg", "-y"] + cmd
    logger.info("Running: %s", " ".join(full_cmd))
    result = subprocess.run(
        full_cmd,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"ffmpeg failed (exit {result.returncode}):\n{result.stderr}"
        )


def get_audio_duration(audio_path: str) -> float:
    """Use ffprobe to get audio duration in seconds."""
    cmd = [
        "ffprobe",
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        audio_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"ffprobe failed (exit {result.returncode}):\n{result.stderr}"
        )
    data = json.loads(result.stdout)
    return float(data["format"]["duration"])


def get_video_duration(video_path: str) -> float:
    """Use ffprobe to get video duration in seconds."""
    cmd = [
        "ffprobe",
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        video_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"ffprobe failed (exit {result.returncode}):\n{result.stderr}"
        )
    data = json.loads(result.stdout)
    return float(data["format"]["duration"])


# ---------------------------------------------------------------------------
# build_*_cmd functions — return the argument list (without "ffmpeg -y")
# ---------------------------------------------------------------------------


def build_ken_burns_cmd(
    image_path: str,
    output_path: str,
    duration: int = 5,
) -> list[str]:
    """Build a zoompan Ken Burns command for a still image.

    Slowly zooms from 1.0x to 1.2x over *duration* seconds at 30 fps.
    """
    total_frames = duration * 30
    return [
        "-loop",
        "1",
        "-i",
        image_path,
        "-vf",
        (f"zoompan=z='min(zoom+0.002,1.2)'" f":d={total_frames}:s=1280x720:fps=30"),
        "-t",
        str(duration),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        output_path,
    ]


def build_scene_clip_cmd(
    visual_path: str,
    audio_path: str,
    output_path: str,
) -> list[str]:
    """Combine a video clip with an audio track (voiceover)."""
    return [
        "-i",
        visual_path,
        "-i",
        audio_path,
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-shortest",
        output_path,
    ]


def build_concat_cmd(
    clip_paths: list[str],
    output_path: str,
) -> list[str]:
    """Concatenate clips using the concat demuxer via a temporary file list.

    Returns a command that references a concat list file. The caller
    should ensure the file exists before running the command — the
    wrapper function ``concat_clips`` handles this automatically.
    """
    # We use a deterministic temp path so tests can inspect the command.
    concat_list_path = str(
        Path(output_path).parent / f".concat_{Path(output_path).stem}.txt"
    )
    return [
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        concat_list_path,
        "-c",
        "copy",
        output_path,
    ]


def build_crossfade_concat_cmd(
    clip_paths: list[str],
    output_path: str,
    fade_duration: float = 0.5,
) -> list[str]:
    """Concatenate clips with crossfade transitions between them.

    Uses xfade for smooth visual transitions and concat for audio.
    Falls back to simple copy for a single clip.
    """
    if len(clip_paths) < 2:
        return ["-i", clip_paths[0], "-c", "copy", output_path]

    inputs: list[str] = []
    for clip in clip_paths:
        inputs.extend(["-i", clip])

    # Build xfade filter chain
    filters = []
    prev_v = "[0:v]"
    for i in range(1, len(clip_paths)):
        out_v = f"[v{i}]"
        filters.append(
            f"{prev_v}[{i}:v]xfade=transition=fade:duration={fade_duration}"
            f":offset={i * 5 - fade_duration}{out_v}"
        )
        prev_v = out_v

    # Concat all audio streams
    audio_inputs = "".join(f"[{i}:a]" for i in range(len(clip_paths)))
    filters.append(f"{audio_inputs}concat=n={len(clip_paths)}:v=0:a=1[aout]")

    return inputs + [
        "-filter_complex",
        ";".join(filters),
        "-map",
        prev_v,
        "-map",
        "[aout]",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        output_path,
    ]


def _video_has_audio(video_path: str) -> bool:
    """Check if a video file contains an audio stream."""
    cmd = [
        "ffprobe",
        "-v",
        "quiet",
        "-select_streams",
        "a",
        "-show_entries",
        "stream=index",
        "-of",
        "csv=p=0",
        video_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return bool(result.stdout.strip())


def build_add_music_cmd(
    video_path: str,
    music_path: str,
    output_path: str,
    music_volume: float = 0.15,
    has_audio: bool = True,
) -> list[str]:
    """Add background music to a video.

    If the video has existing audio (voiceover), mixes it with music.
    If no audio, adds music as the sole audio track.
    """
    if has_audio:
        return [
            "-i",
            video_path,
            "-i",
            music_path,
            "-filter_complex",
            (
                f"[1:a]volume={music_volume}[bg];"
                "[0:a][bg]amix=inputs=2:duration=first:dropout_transition=2[out]"
            ),
            "-map",
            "0:v",
            "-map",
            "[out]",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            output_path,
        ]
    else:
        # No existing audio — just add music at volume
        return [
            "-i",
            video_path,
            "-i",
            music_path,
            "-filter_complex",
            f"[1:a]volume={music_volume}[out]",
            "-map",
            "0:v",
            "-map",
            "[out]",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-shortest",
            output_path,
        ]


def build_adjust_duration_cmd(
    video_path: str,
    output_path: str,
    target_duration: int,
) -> list[str]:
    """Trim or pad a video to match target duration.

    If video is longer, trims it. If shorter, freezes the last frame.
    """
    return [
        "-i",
        video_path,
        "-t",
        str(target_duration),
        "-vf",
        f"tpad=stop_mode=clone:stop_duration={target_duration}",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-an",
        output_path,
    ]


# ---------------------------------------------------------------------------
# Wrapper functions — build command then run
# ---------------------------------------------------------------------------


def create_ken_burns(
    image_path: str,
    output_path: str,
    duration: int = 5,
) -> None:
    """Create a Ken Burns clip from a still image."""
    cmd = build_ken_burns_cmd(image_path, output_path, duration)
    run_ffmpeg(cmd)


def create_scene_clip(
    visual_path: str,
    audio_path: str,
    output_path: str,
) -> None:
    """Combine video + audio into a scene clip."""
    cmd = build_scene_clip_cmd(visual_path, audio_path, output_path)
    run_ffmpeg(cmd)


def concat_clips(
    clip_paths: list[str],
    output_path: str,
) -> None:
    """Concatenate clips. Writes a temporary concat list file, then runs ffmpeg."""
    cmd = build_concat_cmd(clip_paths, output_path)
    # The concat list file path is embedded in the command (-i argument).
    concat_list_path = cmd[cmd.index("-i") + 1]
    with open(concat_list_path, "w") as f:
        for clip in clip_paths:
            f.write(f"file '{clip}'\n")
    try:
        run_ffmpeg(cmd)
    finally:
        Path(concat_list_path).unlink(missing_ok=True)


def crossfade_concat_clips(
    clip_paths: list[str],
    output_path: str,
    fade_duration: float = 0.5,
) -> None:
    """Concatenate clips with crossfade transitions. Falls back to simple concat on error."""
    if len(clip_paths) < 2:
        concat_clips(clip_paths, output_path)
        return
    try:
        # Get durations for accurate xfade offsets
        durations = [get_video_duration(p) for p in clip_paths]
        inputs: list[str] = []
        for clip in clip_paths:
            inputs.extend(["-i", clip])

        # Build xfade filter chain with actual offsets
        filters = []
        prev_v = "[0:v]"
        cumulative_offset = durations[0] - fade_duration
        for i in range(1, len(clip_paths)):
            out_v = f"[v{i}]"
            filters.append(
                f"{prev_v}[{i}:v]xfade=transition=fade:duration={fade_duration}"
                f":offset={cumulative_offset:.2f}{out_v}"
            )
            prev_v = out_v
            if i < len(clip_paths) - 1:
                cumulative_offset += durations[i] - fade_duration

        audio_inputs = "".join(f"[{i}:a]" for i in range(len(clip_paths)))
        filters.append(f"{audio_inputs}concat=n={len(clip_paths)}:v=0:a=1[aout]")

        cmd = inputs + [
            "-filter_complex",
            ";".join(filters),
            "-map",
            prev_v,
            "-map",
            "[aout]",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            output_path,
        ]
        run_ffmpeg(cmd)
    except Exception as e:
        logger.warning(f"Crossfade failed ({e}), falling back to simple concat")
        concat_clips(clip_paths, output_path)


def adjust_video_duration(
    video_path: str,
    output_path: str,
    target_duration: int,
) -> None:
    """Adjust a Veo-generated video to match target duration."""
    cmd = build_adjust_duration_cmd(video_path, output_path, target_duration)
    run_ffmpeg(cmd)


def adjust_audio_duration(
    audio_path: str,
    output_path: str,
    target_duration: float,
) -> None:
    """Adjust audio to match target duration.

    If audio is longer than target, speeds it up with atempo.
    If audio is shorter, pads with silence.
    If close enough (within 0.5s), just trims/pads without tempo change.
    """
    actual = get_audio_duration(audio_path)
    ratio = actual / target_duration if target_duration > 0 else 1.0

    if 0.95 <= ratio <= 1.05:
        # Close enough — just trim or pad
        cmd = [
            "-i",
            audio_path,
            "-af",
            f"apad=whole_dur={target_duration}",
            "-t",
            str(target_duration),
            "-c:a",
            "libmp3lame",
            output_path,
        ]
    elif ratio > 1.0:
        # Audio too long — speed it up (atempo only supports 0.5-2.0 per filter)
        # Chain multiple atempo filters for ratios > 2.0
        remaining = ratio
        filters = []
        while remaining > 1.0:
            step = min(remaining, 2.0)
            filters.append(f"atempo={step:.4f}")
            remaining /= step
        filter_str = ",".join(filters) if filters else "atempo=1.0"
        cmd = [
            "-i",
            audio_path,
            "-af",
            filter_str,
            "-t",
            str(target_duration),
            "-c:a",
            "libmp3lame",
            output_path,
        ]
    else:
        # Audio too short — pad with silence
        cmd = [
            "-i",
            audio_path,
            "-af",
            f"apad=whole_dur={target_duration}",
            "-t",
            str(target_duration),
            "-c:a",
            "libmp3lame",
            output_path,
        ]

    logger.info(
        f"Adjusting audio: {actual:.1f}s -> {target_duration:.1f}s (ratio={ratio:.2f})"
    )
    run_ffmpeg(cmd)


def add_music(
    video_path: str,
    music_path: str,
    output_path: str,
    music_volume: float = 0.15,
) -> None:
    """Add background music to a video. Auto-detects if video has audio."""
    has_audio = _video_has_audio(video_path)
    logger.info(f"Adding music (has_existing_audio={has_audio})")
    cmd = build_add_music_cmd(
        video_path, music_path, output_path, music_volume, has_audio
    )
    run_ffmpeg(cmd)
