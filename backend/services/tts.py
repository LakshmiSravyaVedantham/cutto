"""Text-to-speech service using edge-tts (free Microsoft TTS)."""

import logging

import edge_tts

logger = logging.getLogger(__name__)


async def synthesize_to_file(
    text: str,
    output_path: str,
    voice: str = "en-US-AriaNeural",
) -> str:
    """Synthesize text to an audio file using edge-tts.

    Args:
        text: The text to convert to speech.
        output_path: Path where the audio file will be written.
        voice: The TTS voice to use. Defaults to en-US-AriaNeural.

    Returns:
        The output_path after writing the audio file.
    """
    logger.info(
        "Synthesizing TTS: %d chars -> %s (voice=%s)",
        len(text),
        output_path,
        voice,
    )
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)
    return output_path
