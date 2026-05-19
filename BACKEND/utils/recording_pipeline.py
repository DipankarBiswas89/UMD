"""
Pipeline for storing user recordings and queuing clean samples for future voice retraining.
"""
from __future__ import annotations

import json
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from utils.paths import TRAINING_QUEUE_DIR
from utils.storage import write_recording_metadata

logger = logging.getLogger(__name__)

TRAINING_INDEX = TRAINING_QUEUE_DIR / "index.json"


def _load_index() -> list[dict[str, Any]]:
    if not TRAINING_INDEX.exists():
        return []
    try:
        return json.loads(TRAINING_INDEX.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save_index(entries: list[dict[str, Any]]) -> None:
    TRAINING_INDEX.write_text(json.dumps(entries, indent=2), encoding="utf-8")


def register_recording(
    recording_id: str,
    raw_path: Path,
    processed_path: Path | None,
    *,
    transcript: str | None = None,
    duration_sec: float | None = None,
    tags: list[str] | None = None,
) -> dict[str, Any]:
    """Persist metadata and optionally queue for future fine-tuning."""
    meta = {
        "raw_path": str(raw_path),
        "processed_path": str(processed_path) if processed_path else None,
        "transcript": transcript,
        "duration_sec": duration_sec,
        "tags": tags or [],
        "retrain_status": "pending_review",
    }
    write_recording_metadata(recording_id, meta)

    # Auto-queue if transcript looks usable (clean speech, min length)
    if transcript and len(transcript.strip()) >= 8:
        queue_for_retraining(recording_id, processed_path or raw_path, transcript)

    return {"recording_id": recording_id, **meta}


def queue_for_retraining(
    recording_id: str,
    audio_path: Path,
    transcript: str,
) -> dict[str, Any]:
    """
    Copy processed audio + transcript sidecar into training_queue for Colab retraining.
    """
    dest_audio = TRAINING_QUEUE_DIR / f"{recording_id}.wav"
    dest_text = TRAINING_QUEUE_DIR / f"{recording_id}.txt"

    if audio_path.suffix.lower() != ".wav":
        try:
            from utils.audio_preprocess import preprocess_audio_file

            preprocess_audio_file(audio_path, dest_audio)
        except Exception as exc:
            logger.warning("Could not convert to WAV for training queue: %s", exc)
            shutil.copy2(audio_path, dest_audio)
    else:
        shutil.copy2(audio_path, dest_audio)

    dest_text.write_text(transcript.strip(), encoding="utf-8")

    entry = {
        "recording_id": recording_id,
        "audio": dest_audio.name,
        "transcript_file": dest_text.name,
        "queued_at": datetime.now(timezone.utc).isoformat(),
        "status": "queued",
    }
    index = _load_index()
    index = [e for e in index if e.get("recording_id") != recording_id]
    index.append(entry)
    _save_index(index)
    logger.info("Queued recording %s for future retraining", recording_id)
    return entry


def list_training_queue() -> list[dict[str, Any]]:
    return _load_index()


def mark_retraining_complete(recording_id: str, notes: str = "") -> bool:
    index = _load_index()
    updated = False
    for entry in index:
        if entry.get("recording_id") == recording_id:
            entry["status"] = "used"
            entry["completed_at"] = datetime.now(timezone.utc).isoformat()
            entry["notes"] = notes
            updated = True
    if updated:
        _save_index(index)
    return updated
