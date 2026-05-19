"""
TTS microservice HTTP routes.
"""
from __future__ import annotations

import logging
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from app.audio_utils import apply_noise_reduction_placeholder, cleanup_old_files
from app.config import AUDIO_TTL_HOURS, MAX_TEXT_LENGTH, OUTPUT_DIR, SPEAKERS_DIR
from app.engine import generate_to_file, warmup

logger = logging.getLogger(__name__)
router = APIRouter()

_GENERATED_PREFIXES = ("output_", "test_output", "generated_")


def _valid_speaker_name(name: str) -> bool:
    n = Path(name).name.lower()
    return not any(n.startswith(p) for p in _GENERATED_PREFIXES)


def _resolve_speaker(name: str | None) -> Path:
    if not name:
        for preferred in ("voice.wav", "speaker.wav"):
            p = SPEAKERS_DIR / preferred
            if p.exists():
                return p
        wavs = sorted(SPEAKERS_DIR.glob("*.wav"))
        if wavs:
            return wavs[0]
        raise HTTPException(status_code=404, detail="No speaker WAV found in speakers/")

    safe = Path(name).name
    path = SPEAKERS_DIR / safe
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Speaker not found: {safe}")
    return path


class GenerateVoiceJson(BaseModel):
    text: str = Field(..., min_length=1, max_length=MAX_TEXT_LENGTH)
    speaker_wav: str | None = Field(None, description="Filename in speakers/ directory")
    language: str = "en"


@router.get("/health")
async def health():
    """
    Liveness probe — always HTTP 200 once uvicorn is up.
    Railway must not wait for XTTS weights (can take 10+ minutes on CPU).
    """
    from app.engine import model_status

    info = model_status()
    return {
        "ok": True,
        "service": "tts-service-python311",
        **info,
    }


@router.get("/health/ready")
async def health_ready():
    """Readiness — 200 only when XTTS is loaded and can synthesize."""
    from app.engine import model_status

    info = model_status()
    if info["model_loaded"]:
        return {**info, "ok": True}
    raise HTTPException(
        status_code=503,
        detail=info.get("error") or f"Model not ready (status={info['status']})",
    )


@router.post("/generate-voice")
async def generate_voice(
    text: str = Form(...),
    speaker_wav: str | None = Form(None),
    language: str = Form("en"),
    speaker_file: UploadFile | None = File(None),
):
    """
    Generate cloned voice WAV.

    Provide either:
    - `speaker_wav` = filename already in speakers/
    - `speaker_file` = multipart upload (saved temporarily for this request)
    """
    text = (text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")
    if len(text) > MAX_TEXT_LENGTH:
        raise HTTPException(status_code=400, detail=f"text exceeds {MAX_TEXT_LENGTH} chars")

    speaker_path: Path
    temp_speaker: Path | None = None

    try:
        if speaker_file and speaker_file.filename:
            suffix = Path(speaker_file.filename).suffix.lower() or ".wav"
            if suffix not in (".wav", ".mp3", ".flac"):
                raise HTTPException(status_code=400, detail="speaker_file must be wav/mp3/flac")
            temp_speaker = SPEAKERS_DIR / f"_tmp_{uuid.uuid4().hex}{suffix}"
            data = await speaker_file.read()
            if not data:
                raise HTTPException(status_code=400, detail="Empty speaker file")
            temp_speaker.write_bytes(data)
            speaker_path = temp_speaker
        else:
            speaker_path = _resolve_speaker(speaker_wav)

        await _ensure_model_ready()
        audio_id = uuid.uuid4().hex[:16]
        out_path = OUTPUT_DIR / f"{audio_id}.wav"

        await generate_to_file(text, speaker_path, language=language, output_path=out_path)
        apply_noise_reduction_placeholder(out_path)

        return JSONResponse(
            content={
                "audio_id": audio_id,
                "audio_url": f"/audio/{audio_id}",
                "path": str(out_path),
            }
        )
    except HTTPException:
        raise
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("generate-voice failed")
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {exc}") from exc
    finally:
        if temp_speaker and temp_speaker.exists():
            temp_speaker.unlink(missing_ok=True)


@router.post("/generate-voice/json")
async def generate_voice_json(body: GenerateVoiceJson):
    """JSON variant — speaker_wav must exist in speakers/."""
    await _ensure_model_ready()
    speaker_path = _resolve_speaker(body.speaker_wav)
    audio_id = uuid.uuid4().hex[:16]
    out_path = OUTPUT_DIR / f"{audio_id}.wav"
    await generate_to_file(body.text, speaker_path, language=body.language, output_path=out_path)
    apply_noise_reduction_placeholder(out_path)
    return {
        "audio_id": audio_id,
        "audio_url": f"/audio/{audio_id}",
        "path": str(out_path),
    }


@router.get("/audio/{audio_id}")
async def get_audio(audio_id: str):
    if not audio_id.isalnum() or len(audio_id) > 64:
        raise HTTPException(status_code=400, detail="Invalid audio_id")
    path = OUTPUT_DIR / f"{audio_id}.wav"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Audio not found")
    return FileResponse(path, media_type="audio/wav", filename=f"{audio_id}.wav")


@router.post("/speakers/upload")
async def upload_speaker(file: UploadFile = File(...)):
    """Store a reference speaker clip for cloning."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")
    safe = Path(file.filename).name
    if not _valid_speaker_name(safe):
        raise HTTPException(
            status_code=400,
            detail="Invalid speaker filename (looks like generated output)",
        )
    ext = Path(safe).suffix.lower()
    if ext not in (".wav", ".mp3", ".flac"):
        raise HTTPException(status_code=400, detail="Allowed: .wav, .mp3, .flac")

    dest = SPEAKERS_DIR / safe
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    dest.write_bytes(data)
    logger.info("Speaker uploaded: %s", safe)
    return {"message": "Speaker uploaded", "speaker_wav": safe}


@router.get("/speakers")
async def list_speakers():
    files = [
        f.name
        for f in SPEAKERS_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in (".wav", ".mp3", ".flac")
        and _valid_speaker_name(f.name)
    ]
    return {"speakers": sorted(files)}


async def startup_warmup():
    """Fast startup: serve /health immediately, load XTTS in background."""
    import asyncio

    from app.engine import warmup_background

    cleanup_old_files(OUTPUT_DIR, AUDIO_TTL_HOURS * 3600)
    logger.info("HTTP server up — loading XTTS in background (check /health/ready)")
    asyncio.create_task(warmup_background())


async def _ensure_model_ready() -> None:
    from app.engine import model_status, warmup

    info = model_status()
    if info["model_loaded"]:
        return
    if info["status"] == "failed":
        raise HTTPException(status_code=503, detail=f"XTTS failed to load: {info['error']}")
    if info["status"] == "loading":
        raise HTTPException(status_code=503, detail="XTTS is still loading — retry shortly")
    await warmup()
    info = model_status()
    if not info["model_loaded"]:
        raise HTTPException(status_code=503, detail=info.get("error") or "XTTS not available")
