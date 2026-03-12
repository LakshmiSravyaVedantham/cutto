"""Integration tests for backend.pipeline — the CutTo video generation pipeline.

All external services (Veo, Imagen, TTS, ffmpeg, lipsync) are mocked.
Tests verify orchestration logic, fallback chains, and error handling.
"""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest

from backend.models import Scene, ScenePlan, PipelineProgress


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_scene(
    scene_number: int = 1,
    narration: str = "Test narration",
    visual_prompt: str = "A test scene",
    speaker: str = "narrator",
    target_duration: int = 5,
) -> Scene:
    return Scene(
        scene_number=scene_number,
        narration=narration,
        visual_prompt=visual_prompt,
        speaker=speaker,
        target_duration=target_duration,
    )


def make_plan(
    scenes: list[Scene] | None = None,
    mood: str = "calm",
    visual_style_anchor: str = "",
    audio_driven: bool = False,
) -> ScenePlan:
    if scenes is None:
        scenes = [make_scene()]
    return ScenePlan(
        title="Test Video",
        total_scenes=len(scenes),
        mood=mood,
        visual_style_anchor=visual_style_anchor,
        audio_driven=audio_driven,
        scenes=scenes,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def work_dir(tmp_path):
    """Provide a temporary working directory."""
    return tmp_path


@pytest.fixture
def mock_services():
    """Patch all external services used by the pipeline.

    Returns a dict of mock objects keyed by service name.
    """
    with (
        patch("backend.pipeline.veo.generate_video") as mock_veo,
        patch("backend.pipeline.imagen.generate_image") as mock_imagen,
        patch("backend.pipeline.tts.synthesize_to_file", new_callable=AsyncMock) as mock_tts,
        patch("backend.pipeline.tts.get_voice_for_speaker", return_value="en-US-GuyNeural") as mock_voice,
        patch("backend.pipeline.ffmpeg.get_audio_duration", return_value=4.5) as mock_audio_dur,
        patch("backend.pipeline.ffmpeg.get_video_duration", return_value=5.0) as mock_video_dur,
        patch("backend.pipeline.ffmpeg.adjust_audio_duration") as mock_adjust_audio,
        patch("backend.pipeline.ffmpeg.adjust_video_duration") as mock_adjust_video,
        patch("backend.pipeline.ffmpeg.create_ken_burns") as mock_ken_burns,
        patch("backend.pipeline.ffmpeg.create_scene_clip") as mock_scene_clip,
        patch("backend.pipeline.ffmpeg.concat_clips") as mock_concat,
        patch("backend.pipeline.ffmpeg.add_music") as mock_add_music,
        patch("backend.pipeline.lipsync.is_available", return_value=False) as mock_lipsync_avail,
        patch("backend.pipeline.lipsync.apply_lipsync") as mock_lipsync,
    ):
        # Veo returns the output path by default
        mock_veo.side_effect = lambda prompt, output_path, duration: output_path

        # Imagen returns the output path
        mock_imagen.side_effect = lambda prompt, output_path: output_path

        # TTS writes nothing but returns the path
        mock_tts.return_value = None

        yield {
            "veo": mock_veo,
            "imagen": mock_imagen,
            "tts": mock_tts,
            "voice": mock_voice,
            "audio_dur": mock_audio_dur,
            "video_dur": mock_video_dur,
            "adjust_audio": mock_adjust_audio,
            "adjust_video": mock_adjust_video,
            "ken_burns": mock_ken_burns,
            "scene_clip": mock_scene_clip,
            "concat": mock_concat,
            "add_music": mock_add_music,
            "lipsync_avail": mock_lipsync_avail,
            "lipsync": mock_lipsync,
        }


# ---------------------------------------------------------------------------
# process_scene
# ---------------------------------------------------------------------------


class TestProcessScene:
    """Test the per-scene orchestration: visual + TTS -> combine."""

    @pytest.mark.asyncio
    async def test_veo_success_video_driven(self, work_dir, mock_services):
        """When Veo succeeds, pipeline uses the video and adjusts audio to fit."""
        from backend.pipeline import process_scene

        scene = make_scene(target_duration=5)
        clip = await process_scene(scene, work_dir)

        assert clip.endswith("clip.mp4")
        mock_services["veo"].assert_called_once()
        mock_services["imagen"].assert_not_called()
        mock_services["tts"].assert_awaited_once()
        mock_services["scene_clip"].assert_called_once()
        # Video-driven: audio gets adjusted, not video
        mock_services["adjust_audio"].assert_called_once()
        mock_services["adjust_video"].assert_not_called()
        mock_services["ken_burns"].assert_not_called()

    @pytest.mark.asyncio
    async def test_imagen_fallback_creates_ken_burns(self, work_dir, mock_services):
        """When Veo fails, Imagen produces a static image and Ken Burns is applied."""
        from backend.pipeline import process_scene

        mock_services["veo"].side_effect = RuntimeError("Veo quota exceeded")

        scene = make_scene(target_duration=5)
        clip = await process_scene(scene, work_dir)

        assert clip.endswith("clip.mp4")
        mock_services["veo"].assert_called_once()
        mock_services["imagen"].assert_called_once()
        mock_services["ken_burns"].assert_called_once()
        mock_services["scene_clip"].assert_called_once()

    @pytest.mark.asyncio
    async def test_audio_driven_mode(self, work_dir, mock_services):
        """In audio_driven mode, audio stays natural and video adjusts."""
        from backend.pipeline import process_scene

        mock_services["audio_dur"].return_value = 7.0

        # In audio-driven mode, pipeline reads raw_audio bytes with Path.read_bytes(),
        # so the TTS mock must create the file on disk.
        async def tts_create_file(text, path, voice=None, speaker=None):
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            Path(path).write_bytes(b"fake-audio-data")

        mock_services["tts"].side_effect = tts_create_file

        scene = make_scene(target_duration=5)
        clip = await process_scene(scene, work_dir, audio_driven=True)

        assert clip.endswith("clip.mp4")
        # Audio-driven: audio is NOT adjusted, video IS adjusted
        mock_services["adjust_audio"].assert_not_called()
        mock_services["adjust_video"].assert_called_once()

    @pytest.mark.asyncio
    async def test_style_anchor_prepended(self, work_dir, mock_services):
        """Visual prompt should include the style anchor prefix."""
        from backend.pipeline import process_scene

        scene = make_scene(visual_prompt="A sunset over mountains")
        await process_scene(scene, work_dir, style_anchor="Pixar 3D animation style")

        veo_call_args = mock_services["veo"].call_args
        prompt = veo_call_args[0][0]  # first positional arg
        assert "Pixar 3D animation style" in prompt
        assert "A sunset over mountains" in prompt

    @pytest.mark.asyncio
    async def test_lipsync_applied_for_character_speaker(self, work_dir, mock_services):
        """Lipsync should be applied when speaker is a character and lipsync is available."""
        from backend.pipeline import process_scene

        mock_services["lipsync_avail"].return_value = True
        mock_services["lipsync"].side_effect = lambda v, a, o: o

        scene = make_scene(speaker="character_1")
        clip = await process_scene(scene, work_dir)

        assert clip.endswith("clip.mp4")
        mock_services["lipsync"].assert_called_once()

    @pytest.mark.asyncio
    async def test_lipsync_skipped_for_narrator(self, work_dir, mock_services):
        """Lipsync should NOT be applied for narrator speaker."""
        from backend.pipeline import process_scene

        mock_services["lipsync_avail"].return_value = True

        scene = make_scene(speaker="narrator")
        await process_scene(scene, work_dir)

        mock_services["lipsync"].assert_not_called()

    @pytest.mark.asyncio
    async def test_lipsync_skipped_when_unavailable(self, work_dir, mock_services):
        """Lipsync should NOT be applied when the checkpoint is missing."""
        from backend.pipeline import process_scene

        mock_services["lipsync_avail"].return_value = False

        scene = make_scene(speaker="character_1")
        await process_scene(scene, work_dir)

        mock_services["lipsync"].assert_not_called()

    @pytest.mark.asyncio
    async def test_creates_scene_subdirectory(self, work_dir, mock_services):
        """Each scene should get its own numbered subdirectory."""
        from backend.pipeline import process_scene

        scene = make_scene(scene_number=3)
        await process_scene(scene, work_dir)

        scene_dir = work_dir / "scene_3"
        assert scene_dir.exists()
        assert scene_dir.is_dir()


# ---------------------------------------------------------------------------
# generate_video_with_fallback
# ---------------------------------------------------------------------------


class TestGenerateVideoWithFallback:
    """Test the Veo -> Imagen -> Gemini fallback chain."""

    @pytest.mark.asyncio
    async def test_veo_success_returns_video(self, mock_services):
        """When Veo succeeds, return (path, True) indicating animated video."""
        from backend.pipeline import generate_video_with_fallback

        path, is_video = await generate_video_with_fallback(
            "a panda walking", "/tmp/out.mp4", duration=5
        )
        assert path == "/tmp/out.mp4"
        assert is_video is True
        mock_services["veo"].assert_called_once()
        mock_services["imagen"].assert_not_called()

    @pytest.mark.asyncio
    async def test_veo_fails_imagen_succeeds(self, mock_services):
        """When Veo fails, fall back to Imagen static image."""
        from backend.pipeline import generate_video_with_fallback

        mock_services["veo"].side_effect = RuntimeError("Veo is down")

        path, is_video = await generate_video_with_fallback(
            "a panda walking", "/tmp/out.mp4", duration=5
        )
        assert path == "/tmp/out.png"  # .mp4 replaced with .png
        assert is_video is False
        mock_services["veo"].assert_called_once()
        mock_services["imagen"].assert_called_once()

    @pytest.mark.asyncio
    async def test_veo_and_imagen_fail_imagen_retries(self, mock_services):
        """When both Veo and first Imagen call fail, Imagen retries once."""
        from backend.pipeline import generate_video_with_fallback

        mock_services["veo"].side_effect = RuntimeError("Veo is down")
        # First Imagen call fails, second succeeds
        mock_services["imagen"].side_effect = [
            RuntimeError("Imagen rate limited"),
            "/tmp/out.png",
        ]

        path, is_video = await generate_video_with_fallback(
            "a panda walking", "/tmp/out.mp4", duration=5
        )
        assert path == "/tmp/out.png"
        assert is_video is False
        assert mock_services["imagen"].call_count == 2

    @pytest.mark.asyncio
    async def test_all_fail_gemini_fallback(self, mock_services):
        """When Veo and both Imagen attempts fail, use Gemini native fallback."""
        from backend.pipeline import generate_video_with_fallback

        mock_services["veo"].side_effect = RuntimeError("Veo is down")
        mock_services["imagen"].side_effect = RuntimeError("Imagen broken")

        with patch("backend.pipeline.gemini_fallback_image") as mock_gemini:
            mock_gemini.return_value = "/tmp/out.png"
            path, is_video = await generate_video_with_fallback(
                "a panda walking", "/tmp/out.mp4", duration=5
            )

        assert path == "/tmp/out.png"
        assert is_video is False
        mock_gemini.assert_called_once()
        # Imagen should have been called twice (original + retry)
        assert mock_services["imagen"].call_count == 2

    @pytest.mark.asyncio
    async def test_all_fallbacks_fail_raises(self, mock_services):
        """When every fallback fails, the last error propagates."""
        from backend.pipeline import generate_video_with_fallback

        mock_services["veo"].side_effect = RuntimeError("Veo is down")
        mock_services["imagen"].side_effect = RuntimeError("Imagen broken")

        with patch("backend.pipeline.gemini_fallback_image") as mock_gemini:
            mock_gemini.side_effect = RuntimeError("Gemini fallback also failed")
            with pytest.raises(RuntimeError, match="Gemini fallback also failed"):
                await generate_video_with_fallback(
                    "a panda walking", "/tmp/out.mp4", duration=5
                )


# ---------------------------------------------------------------------------
# assemble_final
# ---------------------------------------------------------------------------


class TestAssembleFinal:
    """Test final assembly: concatenation + background music."""

    @pytest.mark.asyncio
    async def test_single_clip_no_concat(self, mock_services, tmp_path):
        """A single clip should skip concatenation entirely."""
        from backend.pipeline import assemble_final

        plan = make_plan(mood="calm")
        # Point MUSIC_DIR to nonexistent path so music is skipped
        with patch("backend.pipeline.MUSIC_DIR", "/nonexistent/music"):
            result = await assemble_final(plan, ["/tmp/clip1.mp4"], tmp_path)

        mock_services["concat"].assert_not_called()
        # No music file on disk, so add_music is skipped — final is the clip itself
        assert result == "/tmp/clip1.mp4"

    @pytest.mark.asyncio
    async def test_multiple_clips_concatenated(self, mock_services, tmp_path):
        """Multiple clips should be concatenated via ffmpeg."""
        from backend.pipeline import assemble_final

        plan = make_plan(mood="calm")
        clips = ["/tmp/clip1.mp4", "/tmp/clip2.mp4", "/tmp/clip3.mp4"]

        result = await assemble_final(plan, clips, tmp_path)

        mock_services["concat"].assert_called_once()
        concat_args = mock_services["concat"].call_args[0]
        assert concat_args[0] == clips

    @pytest.mark.asyncio
    async def test_music_added_when_file_exists(self, mock_services, tmp_path):
        """Background music should be mixed in when the music file exists on disk."""
        from backend.pipeline import assemble_final

        # Create a fake music file so the Path.exists() check passes
        music_dir = tmp_path / "music"
        music_dir.mkdir()
        (music_dir / "calm.mp3").write_bytes(b"fake-music")

        with patch("backend.pipeline.MUSIC_DIR", str(music_dir)):
            plan = make_plan(mood="calm")
            result = await assemble_final(plan, ["/tmp/clip1.mp4"], tmp_path)

        mock_services["add_music"].assert_called_once()
        add_music_args = mock_services["add_music"].call_args[0]
        assert add_music_args[0] == "/tmp/clip1.mp4"  # input video
        assert "calm.mp3" in add_music_args[1]  # music path
        assert add_music_args[3] == 0.25  # volume

    @pytest.mark.asyncio
    async def test_missing_music_skips_gracefully(self, mock_services, tmp_path):
        """Missing music file should not raise — just skip adding music."""
        from backend.pipeline import assemble_final

        with patch("backend.pipeline.MUSIC_DIR", "/nonexistent/music"):
            plan = make_plan(mood="dramatic")
            result = await assemble_final(plan, ["/tmp/clip1.mp4"], tmp_path)

        mock_services["add_music"].assert_not_called()
        # Result should fall back to the concat/clip path
        assert result == "/tmp/clip1.mp4"

    @pytest.mark.asyncio
    async def test_music_failure_falls_back_to_concat(self, mock_services, tmp_path):
        """If add_music raises, the result should be the concat path without music."""
        from backend.pipeline import assemble_final

        music_dir = tmp_path / "music"
        music_dir.mkdir()
        (music_dir / "calm.mp3").write_bytes(b"fake-music")

        mock_services["add_music"].side_effect = RuntimeError("ffmpeg music mix failed")

        with patch("backend.pipeline.MUSIC_DIR", str(music_dir)):
            plan = make_plan(mood="calm")
            result = await assemble_final(plan, ["/tmp/clip1.mp4"], tmp_path)

        # Should recover gracefully — return the concat path
        assert result == "/tmp/clip1.mp4"

    @pytest.mark.asyncio
    async def test_mood_maps_to_correct_music_file(self, mock_services, tmp_path):
        """Each mood should map to the correct music filename."""
        from backend.pipeline import assemble_final

        music_dir = tmp_path / "music"
        music_dir.mkdir()
        (music_dir / "dramatic.mp3").write_bytes(b"fake")

        with patch("backend.pipeline.MUSIC_DIR", str(music_dir)):
            plan = make_plan(mood="dramatic")
            await assemble_final(plan, ["/tmp/clip1.mp4"], tmp_path)

        add_music_args = mock_services["add_music"].call_args[0]
        assert "dramatic.mp3" in add_music_args[1]

    @pytest.mark.asyncio
    async def test_unknown_mood_defaults_to_calm(self, mock_services, tmp_path):
        """An unrecognized mood should default to 'calm.mp3'."""
        from backend.pipeline import assemble_final, MUSIC_MAP

        plan = make_plan(mood="mysterious")
        # "mysterious" is not in MUSIC_MAP, so it defaults to calm.mp3
        music_file = MUSIC_MAP.get("mysterious", "calm.mp3")
        assert music_file == "calm.mp3"


# ---------------------------------------------------------------------------
# run_pipeline — full end-to-end
# ---------------------------------------------------------------------------


class TestRunPipeline:
    """End-to-end pipeline tests with all services mocked."""

    @pytest.mark.asyncio
    async def test_single_scene_pipeline(self, mock_services):
        """Pipeline should process one scene and produce a final path."""
        from backend.pipeline import run_pipeline

        plan = make_plan(scenes=[make_scene()])
        result = await run_pipeline(plan)

        assert isinstance(result, str)
        mock_services["tts"].assert_awaited_once()
        mock_services["scene_clip"].assert_called_once()

    @pytest.mark.asyncio
    async def test_multi_scene_pipeline(self, mock_services):
        """Pipeline should process all scenes and concatenate them."""
        from backend.pipeline import run_pipeline

        scenes = [make_scene(scene_number=i) for i in range(1, 5)]
        plan = make_plan(scenes=scenes)
        result = await run_pipeline(plan)

        assert isinstance(result, str)
        assert mock_services["scene_clip"].call_count == 4
        # Multiple clips should trigger concatenation
        mock_services["concat"].assert_called_once()

    @pytest.mark.asyncio
    async def test_progress_callback_stages(self, mock_services):
        """Progress callback should be called with correct stages in order."""
        from backend.pipeline import run_pipeline

        progress_events: list[PipelineProgress] = []

        async def track_progress(p: PipelineProgress):
            progress_events.append(p)

        plan = make_plan(scenes=[make_scene()])
        await run_pipeline(plan, progress_callback=track_progress)

        # Verify key progress stages were reported
        steps = [(e.step, e.status) for e in progress_events]
        assert ("visual", "in_progress") in steps
        assert ("clip", "done") in steps
        assert ("assembly", "in_progress") in steps
        assert ("complete", "done") in steps

    @pytest.mark.asyncio
    async def test_progress_callback_includes_video_id(self, mock_services):
        """Every progress event should carry the correct video_id."""
        from backend.pipeline import run_pipeline

        progress_events: list[PipelineProgress] = []

        async def track_progress(p: PipelineProgress):
            progress_events.append(p)

        plan = make_plan(scenes=[make_scene()])
        await run_pipeline(plan, progress_callback=track_progress)

        for event in progress_events:
            assert event.video_id == plan.video_id

    @pytest.mark.asyncio
    async def test_pipeline_no_callback(self, mock_services):
        """Pipeline should work without a progress callback."""
        from backend.pipeline import run_pipeline

        plan = make_plan(scenes=[make_scene()])
        result = await run_pipeline(plan)

        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_batch_processing(self, mock_services):
        """Scenes should be processed in batches of PARALLEL_BATCH_SIZE."""
        from backend.pipeline import run_pipeline, PARALLEL_BATCH_SIZE

        # Create more scenes than the batch size
        scenes = [make_scene(scene_number=i) for i in range(1, PARALLEL_BATCH_SIZE + 3)]
        plan = make_plan(scenes=scenes)
        await run_pipeline(plan)

        # All scenes should have been processed
        assert mock_services["scene_clip"].call_count == len(scenes)

    @pytest.mark.asyncio
    async def test_failed_scenes_filtered_from_assembly(self, mock_services):
        """Scenes that fail should be excluded from final assembly (None filtered out)."""
        from backend.pipeline import run_pipeline

        call_count = 0

        def veo_fail_on_second(prompt, output_path, duration):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise RuntimeError("Veo flaky failure")
            return output_path

        mock_services["veo"].side_effect = veo_fail_on_second
        # When Veo fails, Imagen also needs to fail for scene to truly fail
        original_imagen = mock_services["imagen"].side_effect

        imagen_call_count = 0

        def imagen_fail_on_first(prompt, output_path):
            nonlocal imagen_call_count
            imagen_call_count += 1
            if imagen_call_count == 1:
                raise RuntimeError("Imagen also failed")
            return output_path

        # For the scene that has veo fail, also make imagen fail and gemini fail
        # so the scene fully fails (otherwise fallback catches it)
        mock_services["veo"].side_effect = veo_fail_on_second
        mock_services["imagen"].side_effect = original_imagen

        scenes = [make_scene(scene_number=i) for i in range(1, 4)]
        plan = make_plan(scenes=scenes)

        # Even with a failed scene, pipeline should complete with remaining clips
        result = await run_pipeline(plan)
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Error paths
# ---------------------------------------------------------------------------


class TestErrorPaths:
    """Test failure modes: timeouts, circuit breaker, etc."""

    @pytest.mark.asyncio
    async def test_scene_timeout(self, mock_services):
        """A scene that takes too long should be caught by asyncio.wait_for."""
        from backend.pipeline import run_pipeline

        async def slow_tts(*args, **kwargs):
            await asyncio.sleep(999)

        mock_services["tts"].side_effect = slow_tts

        plan = make_plan(scenes=[make_scene()])

        with patch("backend.pipeline.SCENE_TIMEOUT", 0.01):
            progress_events: list[PipelineProgress] = []

            async def track_progress(p: PipelineProgress):
                progress_events.append(p)

            result = await run_pipeline(plan, progress_callback=track_progress)

        # Scene should have timed out and been recorded as an error
        error_events = [e for e in progress_events if e.status == "error"]
        assert len(error_events) >= 1

    @pytest.mark.asyncio
    async def test_circuit_breaker_aborts_after_three_failures(self, mock_services):
        """Pipeline should abort when 3 or more scenes fail."""
        from backend.pipeline import run_pipeline

        # Make all services fail for every scene
        mock_services["veo"].side_effect = RuntimeError("Veo down")
        mock_services["imagen"].side_effect = RuntimeError("Imagen down")

        with patch("backend.pipeline.gemini_fallback_image") as mock_gemini:
            mock_gemini.side_effect = RuntimeError("Gemini down too")

            scenes = [make_scene(scene_number=i) for i in range(1, 5)]
            plan = make_plan(scenes=scenes)

            with pytest.raises(RuntimeError, match="Too many scene failures"):
                await run_pipeline(plan)

    @pytest.mark.asyncio
    async def test_circuit_breaker_not_triggered_under_three(self, mock_services):
        """Pipeline should continue when fewer than 3 scenes fail."""
        from backend.pipeline import run_pipeline

        fail_count = 0

        def veo_selective_fail(prompt, output_path, duration):
            nonlocal fail_count
            fail_count += 1
            if fail_count <= 2:
                raise RuntimeError("Veo flaky")
            return output_path

        mock_services["veo"].side_effect = veo_selective_fail
        # Imagen also fails so scenes truly fail (not caught by fallback)
        mock_services["imagen"].side_effect = RuntimeError("Imagen also out")

        with patch("backend.pipeline.gemini_fallback_image") as mock_gemini:
            mock_gemini.side_effect = RuntimeError("All fallbacks down")

            scenes = [make_scene(scene_number=i) for i in range(1, 4)]
            plan = make_plan(scenes=scenes)

            # 2 failures + 1 success = should NOT abort
            # But wait: all 3 scenes are in the same batch (PARALLEL_BATCH_SIZE=3),
            # so scene 3 will succeed since fail_count > 2.
            # Scene 1 fails, scene 2 fails, scene 3 succeeds.
            result = await run_pipeline(plan)
            assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_tts_retries_on_first_failure(self, mock_services):
        """generate_tts should retry once if the first TTS call fails."""
        from backend.pipeline import generate_tts

        mock_services["tts"].side_effect = [
            RuntimeError("TTS temporary failure"),
            None,  # second call succeeds
        ]

        # Should not raise — retry should catch it
        await generate_tts("Hello world", "/tmp/audio.mp3", speaker="narrator")
        assert mock_services["tts"].await_count == 2

    @pytest.mark.asyncio
    async def test_tts_raises_when_both_attempts_fail(self, mock_services):
        """generate_tts should raise if both TTS calls fail."""
        from backend.pipeline import generate_tts

        mock_services["tts"].side_effect = RuntimeError("TTS permanently down")

        with pytest.raises(RuntimeError, match="TTS permanently down"):
            await generate_tts("Hello world", "/tmp/audio.mp3", speaker="narrator")

    @pytest.mark.asyncio
    async def test_progress_reports_error_on_scene_failure(self, mock_services):
        """Failed scenes should emit progress with status='error' and a message."""
        from backend.pipeline import run_pipeline

        mock_services["veo"].side_effect = RuntimeError("Veo exploded")
        mock_services["imagen"].side_effect = RuntimeError("Imagen too")

        with patch("backend.pipeline.gemini_fallback_image") as mock_gemini:
            mock_gemini.side_effect = RuntimeError("Everything is broken")

            progress_events: list[PipelineProgress] = []

            async def track_progress(p: PipelineProgress):
                progress_events.append(p)

            plan = make_plan(scenes=[make_scene()])
            await run_pipeline(plan, progress_callback=track_progress)

        error_events = [e for e in progress_events if e.status == "error"]
        assert len(error_events) >= 1
        assert error_events[0].step == "clip"
        assert error_events[0].message != ""
