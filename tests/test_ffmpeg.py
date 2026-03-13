"""Tests for backend.services.ffmpeg module."""

import subprocess
from pathlib import Path

import pytest

from backend.services.ffmpeg import (
    build_add_music_cmd,
    build_concat_cmd,
    build_ken_burns_cmd,
    build_scene_clip_cmd,
    extract_thumbnail,
    get_audio_duration,
    run_ffmpeg,
)

# ---------------------------------------------------------------------------
# build_ken_burns_cmd
# ---------------------------------------------------------------------------


class TestBuildKenBurnsCmd:
    def test_default_duration(self):
        cmd = build_ken_burns_cmd("/tmp/img.png", "/tmp/out.mp4")
        assert cmd[0:2] == ["-loop", "1"]
        assert "-i" in cmd
        assert cmd[cmd.index("-i") + 1] == "/tmp/img.png"
        assert "-vf" in cmd
        assert "-t" in cmd
        assert cmd[cmd.index("-t") + 1] == "5"
        assert cmd[-1] == "/tmp/out.mp4"

    def test_custom_duration(self):
        cmd = build_ken_burns_cmd("/tmp/img.png", "/tmp/out.mp4", duration=10)
        assert cmd[cmd.index("-t") + 1] == "10"
        vf = cmd[cmd.index("-vf") + 1]
        # 10 seconds * 30 fps = 300 frames
        assert "d=300" in vf

    def test_contains_zoompan_filter(self):
        cmd = build_ken_burns_cmd("/tmp/img.png", "/tmp/out.mp4")
        vf = cmd[cmd.index("-vf") + 1]
        assert "zoompan" in vf
        assert "1280x720" in vf
        assert "fps=30" in vf

    def test_codec_and_pixel_format(self):
        cmd = build_ken_burns_cmd("/tmp/img.png", "/tmp/out.mp4")
        assert "-c:v" in cmd
        assert cmd[cmd.index("-c:v") + 1] == "libx264"
        assert "-pix_fmt" in cmd
        assert cmd[cmd.index("-pix_fmt") + 1] == "yuv420p"


# ---------------------------------------------------------------------------
# build_scene_clip_cmd
# ---------------------------------------------------------------------------


class TestBuildSceneClipCmd:
    def test_structure(self):
        cmd = build_scene_clip_cmd("/tmp/vid.mp4", "/tmp/vo.mp3", "/tmp/out.mp4")
        # Two -i inputs
        i_indices = [i for i, v in enumerate(cmd) if v == "-i"]
        assert len(i_indices) == 2
        assert cmd[i_indices[0] + 1] == "/tmp/vid.mp4"
        assert cmd[i_indices[1] + 1] == "/tmp/vo.mp3"

    def test_shortest_flag(self):
        cmd = build_scene_clip_cmd("/tmp/vid.mp4", "/tmp/vo.mp3", "/tmp/out.mp4")
        assert "-shortest" in cmd

    def test_output_path(self):
        cmd = build_scene_clip_cmd("/tmp/vid.mp4", "/tmp/vo.mp3", "/tmp/scene.mp4")
        assert cmd[-1] == "/tmp/scene.mp4"

    def test_audio_codec(self):
        cmd = build_scene_clip_cmd("/tmp/vid.mp4", "/tmp/vo.mp3", "/tmp/out.mp4")
        assert "-c:a" in cmd
        assert cmd[cmd.index("-c:a") + 1] == "aac"


# ---------------------------------------------------------------------------
# build_concat_cmd
# ---------------------------------------------------------------------------


class TestBuildConcatCmd:
    def test_structure(self):
        clips = ["/tmp/a.mp4", "/tmp/b.mp4", "/tmp/c.mp4"]
        cmd = build_concat_cmd(clips, "/tmp/final.mp4")
        assert "-f" in cmd
        assert cmd[cmd.index("-f") + 1] == "concat"
        assert "-safe" in cmd
        assert cmd[cmd.index("-safe") + 1] == "0"

    def test_output_path(self):
        cmd = build_concat_cmd(["/tmp/a.mp4"], "/tmp/out.mp4")
        assert cmd[-1] == "/tmp/out.mp4"

    def test_concat_list_file_path(self):
        cmd = build_concat_cmd(["/tmp/a.mp4"], "/tmp/out.mp4")
        concat_file = cmd[cmd.index("-i") + 1]
        assert concat_file.endswith(".txt")
        assert "concat_" in concat_file

    def test_copy_codec(self):
        cmd = build_concat_cmd(["/tmp/a.mp4"], "/tmp/out.mp4")
        assert "-c" in cmd
        assert cmd[cmd.index("-c") + 1] == "copy"


# ---------------------------------------------------------------------------
# build_add_music_cmd
# ---------------------------------------------------------------------------


class TestBuildAddMusicCmd:
    def test_structure(self):
        cmd = build_add_music_cmd("/tmp/vid.mp4", "/tmp/bg.mp3", "/tmp/out.mp4")
        i_indices = [i for i, v in enumerate(cmd) if v == "-i"]
        assert len(i_indices) == 2
        assert cmd[i_indices[0] + 1] == "/tmp/vid.mp4"
        assert cmd[i_indices[1] + 1] == "/tmp/bg.mp3"

    def test_default_volume(self):
        cmd = build_add_music_cmd("/tmp/vid.mp4", "/tmp/bg.mp3", "/tmp/out.mp4")
        fc = cmd[cmd.index("-filter_complex") + 1]
        assert "volume=0.15" in fc

    def test_custom_volume(self):
        cmd = build_add_music_cmd(
            "/tmp/vid.mp4", "/tmp/bg.mp3", "/tmp/out.mp4", music_volume=0.3
        )
        fc = cmd[cmd.index("-filter_complex") + 1]
        assert "volume=0.3" in fc

    def test_amix_filter(self):
        cmd = build_add_music_cmd("/tmp/vid.mp4", "/tmp/bg.mp3", "/tmp/out.mp4")
        fc = cmd[cmd.index("-filter_complex") + 1]
        assert "amix" in fc
        assert "duration=first" in fc

    def test_map_flags(self):
        cmd = build_add_music_cmd("/tmp/vid.mp4", "/tmp/bg.mp3", "/tmp/out.mp4")
        map_indices = [i for i, v in enumerate(cmd) if v == "-map"]
        assert len(map_indices) == 2
        assert cmd[map_indices[0] + 1] == "0:v"
        assert cmd[map_indices[1] + 1] == "[out]"

    def test_output_path(self):
        cmd = build_add_music_cmd("/tmp/vid.mp4", "/tmp/bg.mp3", "/tmp/final.mp4")
        assert cmd[-1] == "/tmp/final.mp4"


# ---------------------------------------------------------------------------
# run_ffmpeg
# ---------------------------------------------------------------------------


class TestRunFfmpeg:
    def test_raises_on_bad_command(self):
        with pytest.raises(RuntimeError, match="ffmpeg failed"):
            run_ffmpeg(["-i", "/nonexistent/file.mp4", "/tmp/out.mp4"])

    def test_successful_command(self, tmp_path):
        """Generate a 1-second silent video to prove run_ffmpeg works."""
        out = str(tmp_path / "test.mp4")
        run_ffmpeg(
            [
                "-f",
                "lavfi",
                "-i",
                "color=c=black:s=320x240:d=1",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                out,
            ]
        )
        assert (tmp_path / "test.mp4").exists()


# ---------------------------------------------------------------------------
# get_audio_duration
# ---------------------------------------------------------------------------


class TestGetAudioDuration:
    @pytest.fixture(scope="class")
    def test_audio(self, tmp_path_factory):
        """Create a 2-second 440Hz sine wave MP3."""
        audio_path = str(tmp_path_factory.mktemp("audio") / "test.mp3")
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=440:duration=2",
                audio_path,
            ],
            capture_output=True,
            check=True,
        )
        return audio_path

    def test_returns_float(self, test_audio):
        duration = get_audio_duration(test_audio)
        assert isinstance(duration, float)

    def test_approximately_two_seconds(self, test_audio):
        duration = get_audio_duration(test_audio)
        assert 1.9 <= duration <= 2.2

    def test_raises_on_missing_file(self):
        with pytest.raises(RuntimeError, match="ffprobe failed"):
            get_audio_duration("/nonexistent/audio.mp3")


# ---------------------------------------------------------------------------
# extract_thumbnail
# ---------------------------------------------------------------------------


class TestExtractThumbnail:
    @pytest.fixture(scope="class")
    def test_video(self, tmp_path_factory):
        """Create a 2-second black video for thumbnail extraction tests."""
        video_path = str(tmp_path_factory.mktemp("video") / "test.mp4")
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "color=c=blue:s=640x480:d=2",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                video_path,
            ],
            capture_output=True,
            check=True,
        )
        return video_path

    def test_creates_thumbnail_file(self, test_video, tmp_path):
        """extract_thumbnail should create a JPEG file on disk."""
        thumb_path = str(tmp_path / "thumb.jpg")
        extract_thumbnail(test_video, thumb_path)
        assert Path(thumb_path).exists()
        assert Path(thumb_path).stat().st_size > 0

    def test_thumbnail_is_jpeg(self, test_video, tmp_path):
        """Output file should start with JPEG magic bytes."""
        thumb_path = str(tmp_path / "thumb.jpg")
        extract_thumbnail(test_video, thumb_path)
        data = Path(thumb_path).read_bytes()
        # JPEG files start with FF D8
        assert data[:2] == b"\xff\xd8"

    def test_raises_on_missing_video(self, tmp_path):
        """extract_thumbnail should raise RuntimeError for nonexistent input."""
        thumb_path = str(tmp_path / "thumb.jpg")
        with pytest.raises(RuntimeError, match="ffmpeg failed"):
            extract_thumbnail("/nonexistent/video.mp4", thumb_path)
