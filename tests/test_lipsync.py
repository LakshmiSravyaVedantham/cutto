"""Tests for the Wav2Lip lipsync wrapper."""

from pathlib import Path
from unittest.mock import patch


def test_is_available_requires_all_runtime_assets(tmp_path):
    from backend.services import lipsync

    wav2lip_dir = tmp_path / "wav2lip_repo"
    checkpoint = wav2lip_dir / "checkpoints" / "wav2lip_gan.pth"
    inference_script = wav2lip_dir / "inference.py"
    face_detector = wav2lip_dir / "face_detection" / "detection" / "sfd" / "s3fd.pth"

    inference_script.parent.mkdir(parents=True, exist_ok=True)
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    face_detector.parent.mkdir(parents=True, exist_ok=True)

    with (
        patch.object(lipsync, "WAV2LIP_DIR", wav2lip_dir),
        patch.object(lipsync, "CHECKPOINT", checkpoint),
        patch.object(lipsync, "FACE_DET_CHECKPOINT", face_detector),
    ):
        assert not lipsync.is_available()

        inference_script.write_text("print('ok')\n")
        checkpoint.write_bytes(b"weights")
        face_detector.write_bytes(b"detector")

        assert lipsync.is_available()


def test_apply_lipsync_uses_tuned_batch_sizes_and_timeout(tmp_path):
    from backend.services import lipsync

    input_video = tmp_path / "input.mp4"
    input_audio = tmp_path / "input.mp3"
    output_video = tmp_path / "output.mp4"
    inference_script = tmp_path / "wav2lip_repo" / "inference.py"
    checkpoint = tmp_path / "wav2lip_repo" / "checkpoints" / "wav2lip_gan.pth"
    face_detector = (
        tmp_path / "wav2lip_repo" / "face_detection" / "detection" / "sfd" / "s3fd.pth"
    )

    input_video.write_bytes(b"video")
    input_audio.write_bytes(b"audio")
    inference_script.parent.mkdir(parents=True, exist_ok=True)
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    face_detector.parent.mkdir(parents=True, exist_ok=True)
    inference_script.write_text("print('ok')\n")
    checkpoint.write_bytes(b"weights")
    face_detector.write_bytes(b"detector")
    output_video.write_bytes(b"synced")

    with (
        patch.object(lipsync, "WAV2LIP_DIR", tmp_path / "wav2lip_repo"),
        patch.object(lipsync, "CHECKPOINT", checkpoint),
        patch.object(lipsync, "FACE_DET_CHECKPOINT", face_detector),
        patch("backend.services.lipsync.subprocess.run") as mock_run,
    ):
        mock_run.return_value.returncode = 0
        result = lipsync.apply_lipsync(
            str(input_video), str(input_audio), str(output_video)
        )

    assert result == str(output_video)
    cmd = (
        mock_run.call_args.kwargs["args"]
        if "args" in mock_run.call_args.kwargs
        else mock_run.call_args.args[0]
    )
    assert "--face_det_batch_size" in cmd
    assert "--wav2lip_batch_size" in cmd
    assert str(lipsync.WAV2LIP_FACE_DET_BATCH_SIZE) in cmd
    assert str(lipsync.WAV2LIP_INFER_BATCH_SIZE) in cmd
    assert mock_run.call_args.kwargs["timeout"] == lipsync.WAV2LIP_TIMEOUT_SECONDS
