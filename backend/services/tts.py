"""Text-to-speech service with Google Cloud TTS (primary) and edge-tts (fallback)."""

import logging
import os

import edge_tts

logger = logging.getLogger(__name__)

# Google Cloud TTS voice mapping (WaveNet voices for high quality)
CLOUD_VOICE_MAP = {
    "narrator": ("en-US-Wavenet-D", "MALE"),       # Deep, authoritative narrator
    "character_1": ("en-US-Wavenet-F", "FEMALE"),   # Female character
    "character_2": ("en-US-Wavenet-B", "MALE"),     # Male character
    "character_3": ("en-US-Wavenet-E", "FEMALE"),   # Young female
    "character_4": ("en-US-Wavenet-A", "MALE"),     # Older male
}

# edge-tts voice mapping (fallback)
EDGE_VOICE_MAP = {
    "narrator": "en-US-GuyNeural",
    "character_1": "en-US-JennyNeural",
    "character_2": "en-US-ChristopherNeural",
    "character_3": "en-US-SaraNeural",
    "character_4": "en-US-EricNeural",
}

DEFAULT_VOICE = "en-US-AriaNeural"

# Check if Google Cloud TTS is available
_cloud_tts_available = False
try:
    from google.cloud import texttospeech

    if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") or os.environ.get("GOOGLE_API_KEY"):
        _cloud_tts_available = True
        logger.info("Google Cloud TTS available — using as primary")
    else:
        logger.info("No GCP credentials — falling back to edge-tts")
except ImportError:
    logger.info("google-cloud-texttospeech not installed — using edge-tts")


def get_voice_for_speaker(speaker: str) -> str:
    """Get the edge-tts voice for a given speaker role."""
    return EDGE_VOICE_MAP.get(speaker, DEFAULT_VOICE)


async def synthesize_to_file(
    text: str,
    output_path: str,
    voice: str = "en-US-AriaNeural",
    speaker: str = "narrator",
) -> str:
    """Synthesize text to audio. Uses Google Cloud TTS if available, else edge-tts."""
    if _cloud_tts_available:
        try:
            return await _cloud_tts_synthesize(text, output_path, speaker)
        except Exception as e:
            logger.warning(f"Cloud TTS failed ({e}), falling back to edge-tts")

    logger.info(
        "Synthesizing TTS (edge-tts): %d chars -> %s (voice=%s)",
        len(text), output_path, voice,
    )
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)
    return output_path


async def _cloud_tts_synthesize(
    text: str, output_path: str, speaker: str = "narrator",
) -> str:
    """Synthesize using Google Cloud Text-to-Speech API."""
    import asyncio
    from google.cloud import texttospeech

    voice_name, ssml_gender = CLOUD_VOICE_MAP.get(speaker, ("en-US-Wavenet-D", "MALE"))
    gender_enum = (
        texttospeech.SsmlVoiceGender.MALE
        if ssml_gender == "MALE"
        else texttospeech.SsmlVoiceGender.FEMALE
    )

    logger.info(
        "Synthesizing TTS (Cloud): %d chars -> %s (voice=%s)",
        len(text), output_path, voice_name,
    )

    def _sync_synthesize():
        client = texttospeech.TextToSpeechClient()
        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice_params = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name=voice_name,
            ssml_gender=gender_enum,
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=1.0,
            pitch=0.0,
        )
        response = client.synthesize_speech(
            input=synthesis_input, voice=voice_params, audio_config=audio_config,
        )
        with open(output_path, "wb") as f:
            f.write(response.audio_content)
        return output_path

    return await asyncio.to_thread(_sync_synthesize)
