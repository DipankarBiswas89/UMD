"""Service configuration from environment."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SPEAKERS_DIR = Path(os.getenv("SPEAKERS_DIR", str(BASE_DIR / "speakers")))
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", str(BASE_DIR / "generated")))

SPEAKERS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TTS_MODEL = os.getenv("TTS_MODEL", "tts_models/multilingual/multi-dataset/xtts_v2")
TTS_USE_GPU = os.getenv("TTS_USE_GPU", "false").lower() in ("1", "true", "yes")
TTS_LANGUAGE = os.getenv("TTS_LANGUAGE", "en")
AUDIO_TTL_HOURS = int(os.getenv("AUDIO_TTL_HOURS", "24"))
MAX_TEXT_LENGTH = int(os.getenv("MAX_TEXT_LENGTH", "2000"))
