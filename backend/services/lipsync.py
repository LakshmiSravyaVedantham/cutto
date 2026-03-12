"""Lipsync service using Wav2Lip — syncs mouth movement to voiceover audio."""
import logging
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

WAV2LIP_DIR = Path(__file__).resolve().parent.parent.parent / "wav2lip_repo"
CHECKPOINT = WAV2LIP_DIR / "checkpoints" / "wav2lip_gan.pth"


def is_available() -> bool:
    """Check if Wav2Lip model checkpoint exists."""
    return CHECKPOINT.exists()


def apply_lipsync(video_path: str, audio_path: str, output_path: str) -> str:
    """Apply lipsync to a video using Wav2Lip.

    Takes a video with a visible face and an audio file,
    produces a new video with the face lip-synced to the audio.

    Falls back to returning the original video if lipsync fails.
    """
    if not is_available():
        logger.warning("[Lipsync] Wav2Lip checkpoint not found, skipping")
        return video_path

    inference_script = WAV2LIP_DIR / "inference.py"
    if not inference_script.exists():
        logger.warning("[Lipsync] Wav2Lip inference.py not found, skipping")
        return video_path

    cmd = [
        sys.executable,
        str(inference_script),
        "--checkpoint_path", str(CHECKPOINT),
        "--face", video_path,
        "--audio", audio_path,
        "--outfile", output_path,
        "--resize_factor", "1",
        "--nosmooth",
    ]

    logger.info(f"[Lipsync] Running Wav2Lip on {video_path}")
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=str(WAV2LIP_DIR),
        )
        if result.returncode == 0 and Path(output_path).exists():
            size = Path(output_path).stat().st_size
            logger.info(f"[Lipsync] Success: {output_path} ({size:,} bytes)")
            return output_path
        else:
            logger.warning(f"[Lipsync] Failed (exit {result.returncode}): {result.stderr[-500:]}")
            return video_path
    except subprocess.TimeoutExpired:
        logger.warning("[Lipsync] Timed out after 300s, skipping")
        return video_path
    except Exception as e:
        logger.warning(f"[Lipsync] Error: {e}")
        return video_path
