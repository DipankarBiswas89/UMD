"""
In-process Coqui XTTS v2 for Render (Python 3.11) or local monolith deploy.
"""
from __future__ import annotations

import logging
import re
import threading
import time
from pathlib import Path

import numpy as np
import soundfile as sf

logger = logging.getLogger(__name__)

_model = None
_lock = threading.Lock()
_device = "cpu"

TTS_MODEL = __import__("os").getenv("TTS_MODEL", "tts_models/multilingual/multi-dataset/xtts_v2")
TTS_USE_GPU = __import__("os").getenv("TTS_USE_GPU", "false").lower() in ("1", "true", "yes")
TTS_LANGUAGE = __import__("os").getenv("TTS_LANGUAGE", "en")


def is_coqui_installed() -> bool:
    try:
        import TTS  # noqa: F401

        return True
    except ImportError:
        return False


def _patch_torch_load() -> None:
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
    import torch
    import torchaudio

    if getattr(torchaudio.load, "_coqui_sf_patched", False):
        return
    original = torchaudio.load

    def _load(filepath, *args, **kwargs):
        try:
            return original(filepath, *args, **kwargs)
        except ImportError as exc:
            if "torchcodec" not in str(exc).lower():
                raise
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


def _prepare_speaker(speaker_wav: Path) -> Path:
    try:
        info = sf.info(str(speaker_wav))
        if info.samplerate == 22050 and info.channels == 1 and speaker_wav.suffix.lower() == ".wav":
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
    out = speaker_wav.parent / f"{speaker_wav.stem}_xtts_ready.wav"
    sf.write(str(out), data, 22050)
    return out


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

        logger.info("Loading XTTS: %s (gpu=%s)", TTS_MODEL, TTS_USE_GPU)
        started = time.perf_counter()
        tts = TTS(model_name=TTS_MODEL, gpu=TTS_USE_GPU)
        if TTS_USE_GPU and torch.cuda.is_available():
            _model = tts.to("cuda")
            _device = "cuda"
        else:
            _model = tts
            _device = "cpu"
        logger.info("XTTS loaded on %s in %.1fs", _device, time.perf_counter() - started)


def _clean_text(text: str) -> str:
    raw = text.strip()
    if raw.startswith("[") and raw.endswith("]"):
        try:
            import ast

            parsed = ast.literal_eval(raw)
            if isinstance(parsed, (list, tuple)):
                raw = " ".join(str(p).strip() for p in parsed if str(p).strip())
        except Exception:
            pass
    cleaned = re.sub(r"[^\w\s\.,!?;:\-\'\"]", " ", raw)
    return " ".join(cleaned.split())


def synthesize_to_file(text: str, speaker_wav: Path, output_path: Path, language: str | None = None) -> Path:
    load_model_sync()
    import torch

    cleaned = _clean_text(text)
    if not cleaned:
        raise ValueError("Text is empty after normalization")
    if not speaker_wav.exists():
        raise FileNotFoundError(f"Speaker not found: {speaker_wav}")

    speaker = _prepare_speaker(speaker_wav)
    with torch.inference_mode():
        audio = _model.tts(
            text=cleaned,
            speaker_wav=str(speaker),
            language=language or TTS_LANGUAGE,
            split_sentences=True,
        )
    sf.write(str(output_path), np.asarray(audio, dtype=np.float32), 24000)
    return output_path
