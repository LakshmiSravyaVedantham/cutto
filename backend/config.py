import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_IMAGE_MODEL = os.environ.get("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")
IMAGEN_MODEL = os.environ.get("IMAGEN_MODEL", "imagen-4.0-generate-001")
MUSIC_DIR = os.environ.get("MUSIC_DIR", "../music")
DEMO_SECRET = os.environ.get("DEMO_SECRET", "")
MAX_SCENES = 8
MAX_VIDEO_DURATION = 120
