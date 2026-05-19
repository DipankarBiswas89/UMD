"""
XTTS v2 engine — loads once at startup (Python 3.11 only).
"""
from __future__ import annotations

import asyncio
import logging
import re
import threading
import time
import uuid
from pathlib import Path

import numpy as np
import soundfile as sf

from app.config import OUTPUT_DIR, TTS_LANGUAGE, TTS_MODEL, TTS_USE_GPU

logger = logging.getLogger(__name__)

_model = None
_device: str = "cpu"
_lock = threading.Lock()


def _patch_torch_load() -> None:
    """PyTorch 2.6+ defaults weights_only=True; Coqui checkpoints need False."""
    import torch

    if getattr(torch.load, "_coqui_patched", False):
        return
    original = torch.load

    def _load(*args, **kwargs):
        kwargs.setdefault("weights_only", False)
        return original(*args, **kwargs)

    _load._coqui_patched = True
    torch.load = _load


def _patch_torchaudio_load() -> None:
    """torchaudio 2.9+ may require torchcodec; fall back to soundfile for speaker WAV."""
    import torch
    import torchaudio

    if getattr(torchaudio.load, "_coqui_sf_patched", False):
        return

    _original = torchaudio.load

    def _load(filepath, *args, **kwargs):
        try:
            return _original(filepath, *args, **kwargs)
        except ImportError as exc:
            if "torchcodec" not in str(exc).lower():
                raise
            logger.debug("torchaudio.load torchcodec missing; using soundfile for %s", filepath)
            data, sr = sf.read(str(filepath), always_2d=False)
            data = np.asarray(data, dtype=np.float32)
            if data.ndim > 1:
                data = data.mean(axis=1)
            tensor = torch.from_numpy(data)
            if tensor.ndim == 1:
                tensor = tensor.unsqueeze(0)
            return tensor, sr

    _load._coqui_sf_patched = True
    torchaudio.load = _load
    logger.info("Patched torchaudio.load with soundfile fallback (no torchcodec)")


def _prepare_speaker_wav(speaker_wav: Path) -> Path:
    """Ensure speaker reference is mono WAV at 22050 Hz (XTTS-friendly)."""
    if speaker_wav.suffix.lower() == ".wav":
        try:
            info = sf.info(str(speaker_wav))
            if info.samplerate == 22050 and info.channels == 1:
                return speaker_wav
        except Exception:
            pass

    data, sr = sf.read(str(speaker_wav), always_2d=False)
    data = np.asarray(data, dtype=np.float32)
    if data.ndim > 1:
        data = data.mean(axis=1)
    if sr != 22050:
        try:
            import librosa

            data = librosa.resample(data, orig_sr=sr, target_sr=22050)
        except ImportError:
            duration = len(data) / sr
            new_len = int(duration * 22050)
            x_old = np.linspace(0, 1, num=len(data), endpoint=False)
            x_new = np.linspace(0, 1, num=new_len, endpoint=False)
            data = np.interp(x_new, x_old, data).astype(np.float32)
        sr = 22050

    prepared = speaker_wav.parent / f"{speaker_wav.stem}_xtts.wav"
    sf.write(str(prepared), data, sr)
    return prepared


def load_model_sync() -> None:
    global _model, _device
    if _model is not None:
        return

    with _lock:
        if _model is not None:
            return

        _patch_torch_load()
        _patch_torchaudio_load()
        import torch
        from TTS.api import TTS

        logger.info("Loading XTTS model: %s (gpu=%s)", TTS_MODEL, TTS_USE_GPU)
        started = time.perf_counter()
        tts = TTS(model_name=TTS_MODEL, gpu=TTS_USE_GPU)

        if TTS_USE_GPU and torch.cuda.is_available():
            _model = tts.to("cuda")
            _device = "cuda"
        else:
            _model = tts
            _device = "cpu"
            if TTS_USE_GPU:
                logger.warning("GPU requested but CUDA unavailable; using CPU")

        logger.info("XTTS loaded on %s in %.1fs", _device, time.perf_counter() - started)


async def warmup() -> None:
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, load_model_sync)


def _clean_text(text: str) -> str:
    raw = text.strip()
    if raw.startswith("[") and raw.endswith("]"):
        try:
            import ast

            parsed = ast.literal_eval(raw)
            if isinstance(parsed, (list, tuple)):
                raw = " ".join(str(part).strip() for part in parsed if str(part).strip())
        except Exception:
            pass
    cleaned = re.sub(r"[^\w\s\.,!?;:\-\'\"]", " ", raw)
    return " ".join(cleaned.split())


def _synthesize_sync(text: str, speaker_wav: Path, language: str) -> np.ndarray:
    load_model_sync()
    import torch

    cleaned = _clean_text(text)
    if not cleaned:
        raise ValueError("Text is empty after normalization")

    if not speaker_wav.exists():
        raise FileNotFoundError(f"Speaker file not found: {speaker_wav}")

    speaker_path = _prepare_speaker_wav(speaker_wav)

    with torch.inference_mode():
        audio = _model.tts(
            text=cleaned,
            speaker_wav=str(speaker_path),
            language=language or TTS_LANGUAGE,
            split_sentences=True,
        )
    return np.asarray(audio, dtype=np.float32)


async def generate_to_file(
    text: str,
    speaker_wav: Path,
    *,
    language: str | None = None,
    output_path: Path | None = None,
) -> Path:
    """Synthesize speech and write 24 kHz WAV."""
    loop = asyncio.get_event_loop()
    audio = await loop.run_in_executor(
        None,
        lambda: _synthesize_sync(text, speaker_wav, language or TTS_LANGUAGE),
    )

    out = output_path or (OUTPUT_DIR / f"{uuid.uuid4().hex}.wav")
    sf.write(str(out), audio, 24000)
    logger.info("Wrote %s (%.1f KB)", out.name, out.stat().st_size / 1024)
    return out
