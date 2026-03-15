"""Shared Gemini client — Vertex AI (GCP credits) or API key."""

from backend.config import GCP_LOCATION, GCP_PROJECT, GOOGLE_API_KEY, USE_VERTEX_AI

_client = None


def get_client():
    """Return a google.genai.Client configured for Vertex AI or API key."""
    global _client
    if _client is None:
        from google import genai

        if USE_VERTEX_AI:
            _client = genai.Client(
                vertexai=True,
                project=GCP_PROJECT,
                location=GCP_LOCATION,
            )
        else:
            _client = genai.Client(api_key=GOOGLE_API_KEY)
    return _client
