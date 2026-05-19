"""
Voice assistant REST + WebSocket endpoints.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.chat_service import generate_ai_response
from database import AsyncSessionLocal, get_db
from tts_service import get_tts_service
from utils.audio_preprocess import preprocess_audio_file
from utils.paths import GENERATED_AUDIO_DIR
from utils.recording_pipeline import list_training_queue, register_recording
from utils.storage import (
    generated_audio_path,
    new_id,
    resolve_generated_audio,
    resolve_recording,
    save_upload_bytes,
    write_recording_metadata,
)
from utils.whisper_service import transcribe_file

logger = logging.getLogger(__name__)
router = APIRouter(tags=["voice-assistant"])

_audio_locks: dict[str, asyncio.Lock] = {}


class TranscribeRequest(BaseModel):
    recording_id: str | None = None
    language: str | None = None


class GenerateResponseRequest(BaseModel):
    text: str = Field(..., min_length=1)


class GenerateVoiceRequest(BaseModel):
    text: str = Field(..., min_length=1)
    language: str = "en"


class VoiceTurnRequest(BaseModel):
    recording_id: str
    language: str | None = None


def _suffix_from_filename(filename: str | None) -> str:
    if not filename:
        return ".webm"
    return Path(filename).suffix.lower() or ".webm"


@router.post("/record")
async def record_audio(file: UploadFile = File(...)):
    """
    Store a browser microphone recording for transcription / training pipeline.
    """
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty audio file")

    suffix = _suffix_from_filename(file.filename)
    recording_id, raw_path = save_upload_bytes(data, suffix=suffix)

    processed_path = None
    try:
        processed_path = preprocess_audio_file(
            raw_path,
            raw_path.with_name(f"{recording_id}_processed.wav"),
        )
    except Exception as exc:
        logger.warning("Preprocess on record failed: %s", exc)

    register_recording(
        recording_id,
        raw_path,
        processed_path,
        tags=["user_recording"],
    )

    return {
        "recording_id": recording_id,
        "raw_path": raw_path.name,
        "processed_path": processed_path.name if processed_path else None,
        "message": "Recording saved",
    }


@router.post("/transcribe")
async def transcribe(
    file: UploadFile | None = File(None),
    recording_id: str | None = Form(None),
    language: str | None = Form(None),
):
    """
    Transcribe uploaded audio or a previously saved recording_id.
    Applies noise reduction before Whisper.
    """
    processed: Path | None = None
    rec_id: str | None = recording_id

    if file and file.filename:
        data = await file.read()
        if not data:
            raise HTTPException(status_code=400, detail="Empty audio file")
        suffix = _suffix_from_filename(file.filename)
        rec_id, raw_path = save_upload_bytes(data, suffix=suffix)
        processed = preprocess_audio_file(
            raw_path,
            raw_path.with_name(f"{rec_id}_processed.wav"),
        )
    elif rec_id:
        raw_path = resolve_recording(rec_id)
        processed = preprocess_audio_file(
            raw_path,
            raw_path.with_name(f"{rec_id}_processed.wav"),
        )
    else:
        raise HTTPException(
            status_code=400,
            detail="Provide multipart 'file' or form field recording_id",
        )
    result = await transcribe_file(processed, language=language)
    text = result.get("text", "").strip()

    if rec_id:
        register_recording(
            rec_id,
            raw_path,
            processed,
            transcript=text,
        )

    return {
        "recording_id": rec_id,
        "text": text,
        "language": result.get("language"),
        "segments": result.get("segments", []),
    }


@router.post("/generate-response")
async def generate_response_endpoint(
    req: GenerateResponseRequest,
    db: AsyncSession = Depends(get_db),
):
    """Generate AI chat response from transcribed text."""
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")
    result = await generate_ai_response(text, db)
    return {
        "question": text,
        "response": result.get("response", ""),
        "error": result.get("error"),
    }


@router.post("/generate-voice")
async def generate_voice_endpoint(req: GenerateVoiceRequest):
    """Generate cloned voice audio (XTTS v2) and return audio id + URL."""
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")

    tts = get_tts_service()
    voice_sample = tts.voice_sample_path
    voice_tag = ""
    if voice_sample and voice_sample.exists():
        st = voice_sample.stat()
        voice_tag = f"{voice_sample.name}:{int(st.st_mtime)}:{st.st_size}"

    key = hashlib.sha1((voice_tag + "\n" + text).encode("utf-8")).hexdigest()[:16]
    audio_id = key
    out_path = generated_audio_path(audio_id)

    if out_path.exists():
        return {
            "audio_id": audio_id,
            "audio_url": f"/audio/{audio_id}",
            "cached": True,
        }

    lock = _audio_locks.setdefault(audio_id, asyncio.Lock())
    try:
        async with lock:
            if out_path.exists():
                return {
                    "audio_id": audio_id,
                    "audio_url": f"/audio/{audio_id}",
                    "cached": True,
                }
            await tts.generate_speech(text, output_path=out_path)
    except Exception as exc:
        logger.exception("Voice generation failed")
        raise HTTPException(status_code=500, detail=f"Voice generation failed: {exc}") from exc
    finally:
        _audio_locks.pop(audio_id, None)

    return {
        "audio_id": audio_id,
        "audio_url": f"/audio/{audio_id}",
        "cached": False,
    }


@router.get("/audio/{audio_id}")
async def get_audio(audio_id: str):
    """Serve generated cloned-voice audio by id."""
    path = resolve_generated_audio(audio_id)
    return FileResponse(
        path,
        media_type="audio/wav",
        filename=f"{audio_id}.wav",
    )


@router.post("/voice-turn")
async def voice_turn(
    req: VoiceTurnRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Full pipeline in one call: transcribe → AI response → cloned voice.
    Lower round-trips for real-time UX.
    """
    try:
        raw_path = resolve_recording(req.recording_id)
        processed = preprocess_audio_file(
            raw_path,
            raw_path.with_name(f"{req.recording_id}_processed.wav"),
        )
        stt = await transcribe_file(processed, language=req.language)
        user_text = stt.get("text", "").strip()
        if not user_text:
            raise HTTPException(status_code=422, detail="Could not transcribe speech")

        register_recording(
            req.recording_id,
            raw_path,
            processed,
            transcript=user_text,
        )

        ai = await generate_ai_response(user_text, db)
        bot_text = ai.get("response", "").strip() or "No response generated."

        voice_req = GenerateVoiceRequest(text=bot_text)
        voice = await generate_voice_endpoint(voice_req)

        return {
            "recording_id": req.recording_id,
            "transcript": user_text,
            "response": bot_text,
            "audio_id": voice["audio_id"],
            "audio_url": voice["audio_url"],
            "cached": voice.get("cached", False),
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("voice-turn failed for recording %s", req.recording_id)
        raise HTTPException(
            status_code=500,
            detail=f"Voice pipeline failed: {exc}",
        ) from exc


@router.get("/training-queue")
async def training_queue():
    """List recordings queued for future XTTS retraining (Colab)."""
    return {"items": list_training_queue()}


@router.websocket("/ws/voice")
async def voice_websocket(websocket: WebSocket):
    """
    WebSocket for lower-latency voice turns.
    Client sends JSON: { "type": "audio", "data": "<base64>" } or { "type": "recording_id", "id": "..." }
    Server responds with transcript, response, audio_url.
    """
    await websocket.accept()
    try:
        while True:
            raw = await websocket.receive_text()
            payload = json.loads(raw)
            msg_type = payload.get("type")

            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            if msg_type == "interrupt":
                await websocket.send_json({"type": "interrupted"})
                continue

            if msg_type == "recording_id":
                rid = payload.get("recording_id")
                if not rid:
                    await websocket.send_json({"type": "error", "message": "recording_id required"})
                    continue
                await websocket.send_json({"type": "status", "status": "processing"})
                async with AsyncSessionLocal() as db:
                    result = await voice_turn(VoiceTurnRequest(recording_id=rid), db)
                await websocket.send_json({"type": "complete", **result})
                continue

            if msg_type == "audio":
                import base64

                b64 = payload.get("data", "")
                if not b64:
                    await websocket.send_json({"type": "error", "message": "data required"})
                    continue
                data = base64.b64decode(b64)
                suffix = payload.get("suffix", ".webm")
                recording_id, raw_path = save_upload_bytes(data, suffix=suffix)
                processed = preprocess_audio_file(
                    raw_path,
                    raw_path.with_name(f"{recording_id}_processed.wav"),
                )
                await websocket.send_json({"type": "status", "status": "transcribing"})
                stt = await transcribe_file(processed)
                user_text = stt.get("text", "").strip()
                await websocket.send_json(
                    {"type": "transcript", "text": user_text, "recording_id": recording_id}
                )
                if not user_text:
                    await websocket.send_json({"type": "error", "message": "Empty transcript"})
                    continue
                register_recording(recording_id, raw_path, processed, transcript=user_text)
                await websocket.send_json({"type": "status", "status": "thinking"})
                async with AsyncSessionLocal() as db:
                    ai = await generate_ai_response(user_text, db)
                bot_text = ai.get("response", "").strip()
                await websocket.send_json({"type": "response", "text": bot_text})
                await websocket.send_json({"type": "status", "status": "speaking"})
                voice = await generate_voice_endpoint(GenerateVoiceRequest(text=bot_text))
                await websocket.send_json({"type": "complete", "audio_url": voice["audio_url"], **voice})
                continue

            await websocket.send_json({"type": "error", "message": f"Unknown type: {msg_type}"})
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.exception("WebSocket error")
        try:
            await websocket.send_json({"type": "error", "message": str(exc)})
        except Exception:
            pass
