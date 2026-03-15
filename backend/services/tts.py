"""Text-to-speech service with Google Cloud TTS (primary) and edge-tts (fallback)."""

import logging
import os

import edge_tts

logger = logging.getLogger(__name__)

# Google Cloud TTS voice mapping (Journey/Studio voices for ultra-realistic quality)
# Journey voices are the most natural-sounding, trained on real conversations
# Studio voices are studio-grade quality for professional narration
# Fallback to WaveNet if Journey/Studio not available
CLOUD_VOICE_MAP = {
    "narrator": ("en-US-Journey-D", "MALE"),  # Deep, warm narrator — most natural
    "character_1": ("en-US-Journey-F", "FEMALE"),  # Natural female speaker
    "character_2": ("en-US-Journey-D", "MALE"),  # Natural male speaker
    "character_3": ("en-US-Studio-O", "FEMALE"),  # Studio-grade young female
    "character_4": ("en-US-Studio-Q", "MALE"),  # Studio-grade older male
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

# Check if Google Cloud TTS is available (uses REST API with API key)
_cloud_tts_available = bool(os.environ.get("GOOGLE_API_KEY"))
if _cloud_tts_available:
    logger.info("Google Cloud TTS available — using API key via REST")
else:
    logger.info("No GOOGLE_API_KEY — falling back to edge-tts")


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
        len(text),
        output_path,
        voice,
    )
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)
    return output_path


async def _cloud_tts_synthesize(
    text: str,
    output_path: str,
    speaker: str = "narrator",
) -> str:
    """Synthesize using Google Cloud Text-to-Speech REST API with API key."""
    import asyncio
    import base64
    import json
    import urllib.request

    api_key = os.environ.get("GOOGLE_API_KEY", "")
    voice_name, ssml_gender = CLOUD_VOICE_MAP.get(speaker, ("en-US-Wavenet-D", "MALE"))

    logger.info(
        "Synthesizing TTS (Cloud): %d chars -> %s (voice=%s)",
        len(text),
        output_path,
        voice_name,
    )

    def _sync_synthesize():
        url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={api_key}"
        payload = json.dumps(
            {
                "input": {"text": text},
                "voice": {
                    "languageCode": "en-US",
                    "name": voice_name,
                    "ssmlGender": ssml_gender,
                },
                "audioConfig": {
                    "audioEncoding": "MP3",
                    "speakingRate": 0.92,  # Slightly slower for natural delivery
                    "pitch": -1.0,  # Slightly deeper for cinematic feel
                    "volumeGainDb": 1.0,  # Slight boost for clarity
                    "effectsProfileId": ["large-home-entertainment-class-device"],
                },
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        audio_bytes = base64.b64decode(result["audioContent"])
        with open(output_path, "wb") as f:
            f.write(audio_bytes)
        return output_path

    return await asyncio.to_thread(_sync_synthesize)
