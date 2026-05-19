"""
File storage helpers for recordings and generated audio assets.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from utils.paths import (
    GENERATED_AUDIO_DIR,
    MAX_UPLOAD_BYTES,
    RECORDINGS_META_DIR,
    UPLOADS_DIR,
)


def new_id() -> str:
    return uuid.uuid4().hex


def recording_path(recording_id: str, ext: str = ".webm") -> Path:
    return UPLOADS_DIR / f"{recording_id}{ext}"


def generated_audio_path(audio_id: str) -> Path:
    return GENERATED_AUDIO_DIR / f"{audio_id}.wav"


def save_upload_bytes(data: bytes, suffix: str = ".webm") -> tuple[str, Path]:
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max size is {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.",
        )
    recording_id = new_id()
    path = recording_path(recording_id, suffix)
    path.write_bytes(data)
    return recording_id, path


def write_recording_metadata(recording_id: str, meta: dict[str, Any]) -> Path:
    meta_path = RECORDINGS_META_DIR / f"{recording_id}.json"
    payload = {
        "recording_id": recording_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        **meta,
    }
    meta_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return meta_path


def read_recording_metadata(recording_id: str) -> dict[str, Any] | None:
    meta_path = RECORDINGS_META_DIR / f"{recording_id}.json"
    if not meta_path.exists():
        return None
    return json.loads(meta_path.read_text(encoding="utf-8"))


def resolve_recording(recording_id: str) -> Path:
    for ext in (".webm", ".wav", ".mp3", ".ogg", ".m4a", ".flac"):
        candidate = recording_path(recording_id, ext)
        if candidate.exists():
            return candidate
    raise HTTPException(status_code=404, detail="Recording not found")


def resolve_generated_audio(audio_id: str) -> Path:
    path = generated_audio_path(audio_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Audio not found")
    return path
