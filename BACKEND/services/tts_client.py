"""
HTTP client for the Python 3.11 TTS microservice (Coqui XTTS v2).
Main backend (Python 3.12) must never import TTS/torch directly.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

TTS_SERVICE_URL = os.getenv("TTS_SERVICE_URL", "http://127.0.0.1:8001").rstrip("/")
TTS_REQUEST_TIMEOUT = float(os.getenv("TTS_REQUEST_TIMEOUT", "300"))


class TTSClientError(Exception):
    """Raised when the TTS microservice returns an error."""


async def health_check() -> dict:
    async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as client:
        resp = await client.get(f"{TTS_SERVICE_URL}/health")
        resp.raise_for_status()
        data = resp.json()
        data["service_up"] = True
        try:
            ready_resp = await client.get(f"{TTS_SERVICE_URL}/health/ready")
            data["model_ready"] = ready_resp.status_code == 200
        except Exception:
            data["model_ready"] = bool(data.get("model_loaded"))
        data["ok"] = data.get("service_up") and data.get("model_ready", False)
        return data


async def upload_speaker(local_path: Path) -> dict:
    """Sync speaker WAV to TTS microservice speakers/ directory."""
    if not local_path.exists():
        raise FileNotFoundError(f"Speaker file not found: {local_path}")

    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
        with open(local_path, "rb") as f:
            resp = await client.post(
                f"{TTS_SERVICE_URL}/speakers/upload",
                files={"file": (local_path.name, f, "audio/wav")},
            )
        if resp.status_code >= 400:
            detail = resp.text
            try:
                detail = resp.json().get("detail", detail)
            except Exception:
                pass
            raise TTSClientError(f"Speaker upload failed: {detail}")
        return resp.json()


async def generate_voice(
    text: str,
    speaker_wav_path: Path | None = None,
    *,
    language: str = "en",
) -> tuple[bytes, str]:
    """
    Call TTS microservice POST /generate-voice, then download WAV bytes.
    Returns (audio_bytes, audio_id).
    """
    text = text.strip()
    if not text:
        raise ValueError("text is required")

    timeout = httpx.Timeout(TTS_REQUEST_TIMEOUT)
    async with httpx.AsyncClient(timeout=timeout) as client:
        if speaker_wav_path and speaker_wav_path.exists():
            with open(speaker_wav_path, "rb") as f:
                resp = await client.post(
                    f"{TTS_SERVICE_URL}/generate-voice",
                    data={"text": text, "language": language},
                    files={"speaker_file": (speaker_wav_path.name, f, "audio/wav")},
                )
        else:
            speaker_name = speaker_wav_path.name if speaker_wav_path else None
            resp = await client.post(
                f"{TTS_SERVICE_URL}/generate-voice",
                data={
                    "text": text,
                    "language": language,
                    **({"speaker_wav": speaker_name} if speaker_name else {}),
                },
            )

        if resp.status_code >= 400:
            detail = resp.text
            try:
                detail = resp.json().get("detail", detail)
            except Exception:
                pass
            raise TTSClientError(f"TTS generate failed ({resp.status_code}): {detail}")

        meta = resp.json()
        audio_id = meta.get("audio_id")
        if not audio_id:
            raise TTSClientError("TTS service returned no audio_id")

        audio_resp = await client.get(f"{TTS_SERVICE_URL}/audio/{audio_id}")
        if audio_resp.status_code >= 400:
            raise TTSClientError(f"Failed to fetch audio {audio_id}")
        return audio_resp.content, audio_id


async def generate_voice_to_path(
    text: str,
    output_path: Path,
    speaker_wav_path: Path | None = None,
    *,
    language: str = "en",
) -> Path:
    """Generate voice and write to output_path."""
    data, _ = await generate_voice(text, speaker_wav_path, language=language)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(data)
    return output_path
