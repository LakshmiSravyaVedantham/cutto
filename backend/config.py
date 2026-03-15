import os

from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")

# Vertex AI config — uses GCP credits instead of API key
USE_VERTEX_AI = os.environ.get("USE_VERTEX_AI", "").lower() in ("1", "true", "yes")
GCP_PROJECT = os.environ.get("GCP_PROJECT", "gen-lang-client-0513383582")
GCP_LOCATION = os.environ.get("GCP_LOCATION", "us-central1")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_IMAGE_MODEL = os.environ.get("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")
IMAGEN_MODEL = os.environ.get("IMAGEN_MODEL", "imagen-4.0-generate-001")
VEO_MODEL = os.environ.get("VEO_MODEL", "veo-2.0-generate-001")
_music_raw = os.environ.get("MUSIC_DIR", "./music")
MUSIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", _music_raw))
DEMO_SECRET = os.environ.get("DEMO_SECRET", "")
PIPELINE_PARALLEL_BATCH_SIZE = int(os.environ.get("PIPELINE_PARALLEL_BATCH_SIZE", "4"))
SCENE_TIMEOUT_SECONDS = int(os.environ.get("SCENE_TIMEOUT_SECONDS", "420"))
WAV2LIP_TIMEOUT_SECONDS = int(os.environ.get("WAV2LIP_TIMEOUT_SECONDS", "600"))
WAV2LIP_FACE_DET_BATCH_SIZE = int(os.environ.get("WAV2LIP_FACE_DET_BATCH_SIZE", "4"))
WAV2LIP_INFER_BATCH_SIZE = int(os.environ.get("WAV2LIP_INFER_BATCH_SIZE", "16"))
MAX_SCENES = 8
MAX_VIDEO_DURATION = 120
