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
        "-v", "quiet",
        "-print_format", "json",
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
        "-loop", "1",
        "-i", image_path,
        "-vf", (
            f"zoompan=z='min(zoom+0.002,1.2)'"
            f":d={total_frames}:s=1280x720:fps=30"
        ),
        "-t", str(duration),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        output_path,
    ]


def build_scene_clip_cmd(
    visual_path: str,
    audio_path: str,
    output_path: str,
) -> list[str]:
    """Combine a video clip with an audio track (voiceover)."""
    return [
        "-i", visual_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
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
        "-f", "concat",
        "-safe", "0",
        "-i", concat_list_path,
        "-c", "copy",
        output_path,
    ]


def build_add_music_cmd(
    video_path: str,
    music_path: str,
    output_path: str,
    music_volume: float = 0.15,
) -> list[str]:
    """Add background music ducked under existing audio.

    Uses amix to blend the original audio (full volume) with the music
    track scaled to *music_volume*.
    """
    return [
        "-i", video_path,
        "-i", music_path,
        "-filter_complex",
        (
            f"[1:a]volume={music_volume}[bg];"
            "[0:a][bg]amix=inputs=2:duration=first:dropout_transition=2[out]"
        ),
        "-map", "0:v",
        "-map", "[out]",
        "-c:v", "copy",
        "-c:a", "aac",
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


def add_music(
    video_path: str,
    music_path: str,
    output_path: str,
    music_volume: float = 0.15,
) -> None:
    """Add background music to a video."""
    cmd = build_add_music_cmd(video_path, music_path, output_path, music_volume)
    run_ffmpeg(cmd)
