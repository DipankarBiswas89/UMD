"""
Speech-to-text using faster-whisper (local) with async executor wrapper.
"""
from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_whisper_model = None
_model_lock = asyncio.Lock()


def _get_model_config() -> dict[str, Any]:
    return {
        "model_size": os.getenv("WHISPER_MODEL", "base"),
        "device": os.getenv("WHISPER_DEVICE", "auto"),
        "compute_type": os.getenv("WHISPER_COMPUTE_TYPE", "int8"),
        "language": os.getenv("WHISPER_LANGUAGE") or None,
    }


def _load_model_sync():
    global _whisper_model
    if _whisper_model is not None:
        return _whisper_model

    from faster_whisper import WhisperModel

    cfg = _get_model_config()
    device = cfg["device"]
    if device == "auto":
        try:
            import torch

            device = "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            device = "cpu"

    logger.info(
        "Loading faster-whisper model=%s device=%s",
        cfg["model_size"],
        device,
    )
    _whisper_model = WhisperModel(
        cfg["model_size"],
        device=device,
        compute_type=cfg["compute_type"],
        download_root=str(
            Path(__file__).resolve().parent.parent / "models" / "whisper"
        ),
    )
    return _whisper_model


async def warmup_whisper() -> None:
    async with _model_lock:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _load_model_sync)


def _transcribe_sync(audio_path: Path, language: str | None = None) -> dict[str, Any]:
    model = _load_model_sync()
    cfg = _get_model_config()
    lang = language or cfg["language"]

    segments, info = model.transcribe(
        str(audio_path),
        language=lang,
        vad_filter=True,
        beam_size=5,
    )
    text_parts: list[str] = []
    segment_list: list[dict[str, Any]] = []
    for seg in segments:
        text_parts.append(seg.text.strip())
        segment_list.append(
            {
                "start": seg.start,
                "end": seg.end,
                "text": seg.text.strip(),
            }
        )

    full_text = " ".join(t for t in text_parts if t).strip()
    return {
        "text": full_text,
        "language": getattr(info, "language", lang),
        "segments": segment_list,
    }


async def transcribe_file(audio_path: Path, language: str | None = None) -> dict[str, Any]:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, lambda: _transcribe_sync(audio_path, language)
    )
