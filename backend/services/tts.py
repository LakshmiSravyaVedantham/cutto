"""Text-to-speech service using edge-tts (free Microsoft TTS)."""

import logging

import edge_tts

logger = logging.getLogger(__name__)

# Voice mapping for different speakers
VOICE_MAP = {
    "narrator": "en-US-GuyNeural",         # Deep, authoritative narrator
    "character_1": "en-US-JennyNeural",     # Female character
    "character_2": "en-US-ChristopherNeural",  # Male character
    "character_3": "en-US-SaraNeural",      # Young female
    "character_4": "en-US-EricNeural",      # Older male
}

DEFAULT_VOICE = "en-US-AriaNeural"


def get_voice_for_speaker(speaker: str) -> str:
    """Get the TTS voice for a given speaker role."""
    return VOICE_MAP.get(speaker, DEFAULT_VOICE)


async def synthesize_to_file(
    text: str,
    output_path: str,
    voice: str = "en-US-AriaNeural",
) -> str:
    """Synthesize text to an audio file using edge-tts."""
    logger.info(
        "Synthesizing TTS: %d chars -> %s (voice=%s)",
        len(text),
        output_path,
        voice,
    )
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)
    return output_path
