"""
Central path configuration for uploads, generated audio, models, and training data.
"""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

UPLOADS_DIR = BASE_DIR / "uploads"
GENERATED_AUDIO_DIR = BASE_DIR / "generated_audio"
MODELS_DIR = BASE_DIR / "models"
TRAINING_QUEUE_DIR = BASE_DIR / "uploads" / "training_queue"
RECORDINGS_META_DIR = BASE_DIR / "uploads" / "metadata"

for directory in (
    UPLOADS_DIR,
    GENERATED_AUDIO_DIR,
    MODELS_DIR,
    TRAINING_QUEUE_DIR,
    RECORDINGS_META_DIR,
):
    directory.mkdir(parents=True, exist_ok=True)

MAX_UPLOAD_BYTES = int(
    __import__("os").getenv("MAX_UPLOAD_BYTES", str(25 * 1024 * 1024))
)
