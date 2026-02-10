import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"
SFX_LIBRARY_DIR = BASE_DIR / "sfx_library"

UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

MAX_FILE_SIZE_MB = 50
MAX_DURATION_SEC = 600  # 10 minutes
SUPPORTED_FORMATS = {".mp3", ".wav", ".flac", ".ogg", ".m4a"}

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_TIMEOUT_SEC = 12
GEMINI_MODEL = "gemini-2.5-pro"

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_TIMEOUT_SEC = 8

# Auto-delete uploads after 1 hour
FILE_TTL_SEC = 3600
