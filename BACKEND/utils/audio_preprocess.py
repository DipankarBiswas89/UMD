"""
Noise reduction, normalization, and light echo/hum mitigation for microphone input.
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import soundfile as sf

logger = logging.getLogger(__name__)

TARGET_SAMPLE_RATE = 16000

# soundfile cannot decode browser MediaRecorder output
_AV_FORMATS = {".webm", ".ogg", ".m4a", ".mp4", ".opus", ".aac", ".wma"}


def _load_audio_any(input_path: Path) -> tuple[np.ndarray, int]:
    """Load audio from WAV/MP3/FLAC or WebM/Opus (browser mic) via PyAV."""
    suffix = input_path.suffix.lower()

    if suffix not in _AV_FORMATS:
        try:
            audio, sr = sf.read(str(input_path), always_2d=False)
            return _to_mono(np.asarray(audio, dtype=np.float32)), int(sr)
        except Exception as exc:
            logger.debug("soundfile failed for %s: %s", input_path.name, exc)

    try:
        import av
    except ImportError as exc:
        raise RuntimeError(
            "Cannot decode WebM/Opus recordings. Install PyAV: pip install av"
        ) from exc

    container = av.open(str(input_path))
    if not container.streams.audio:
        raise ValueError(f"No audio stream in {input_path.name}")

    stream = container.streams.audio[0]
    chunks: list[np.ndarray] = []
    for frame in container.decode(audio=0):
        arr = frame.to_ndarray()
        if arr.ndim == 2:
            arr = arr.mean(axis=0)
        chunks.append(arr.astype(np.float32))

    if not chunks:
        raise ValueError(f"Empty audio file: {input_path.name}")

    audio = np.concatenate(chunks)
    sr = int(stream.codec_context.sample_rate or TARGET_SAMPLE_RATE)
    return audio.astype(np.float32), sr


def _to_mono(audio: np.ndarray) -> np.ndarray:
    if audio.ndim == 1:
        return audio.astype(np.float32)
    return audio.mean(axis=1).astype(np.float32)


def _resample(audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
    if orig_sr == target_sr:
        return audio
    try:
        import librosa

        return librosa.resample(audio, orig_sr=orig_sr, target_sr=target_sr)
    except ImportError:
        duration = len(audio) / orig_sr
        new_len = int(duration * target_sr)
        x_old = np.linspace(0, 1, num=len(audio), endpoint=False)
        x_new = np.linspace(0, 1, num=new_len, endpoint=False)
        return np.interp(x_new, x_old, audio).astype(np.float32)


def _highpass(audio: np.ndarray, sr: int, cutoff_hz: float = 80.0) -> np.ndarray:
    """Simple high-pass to reduce low-frequency hum."""
    try:
        from scipy.signal import butter, filtfilt

        nyq = 0.5 * sr
        normal_cutoff = cutoff_hz / nyq
        b, a = butter(2, normal_cutoff, btype="high", analog=False)
        return filtfilt(b, a, audio).astype(np.float32)
    except Exception as exc:
        logger.debug("High-pass skipped: %s", exc)
        return audio


def _normalize(audio: np.ndarray, target_peak: float = 0.95) -> np.ndarray:
    peak = float(np.max(np.abs(audio))) if audio.size else 0.0
    if peak < 1e-6:
        return audio
    return (audio / peak * target_peak).astype(np.float32)


def _reduce_noise(audio: np.ndarray, sr: int) -> np.ndarray:
    try:
        import noisereduce as nr

        return nr.reduce_noise(y=audio, sr=sr, stationary=True, prop_decrease=0.75)
    except ImportError:
        logger.warning("noisereduce not installed; skipping noise reduction")
        return audio
    except Exception as exc:
        logger.warning("Noise reduction failed: %s", exc)
        return audio


def preprocess_audio_file(
    input_path: Path,
    output_path: Path | None = None,
    *,
    apply_noise_reduction: bool = True,
) -> Path:
    """
    Load audio, denoise, high-pass, normalize, and write 16 kHz mono WAV.
    Returns path to processed file.
    """
    audio, sr = _load_audio_any(input_path)
    audio = _resample(audio, sr, TARGET_SAMPLE_RATE)
    audio = _highpass(audio, TARGET_SAMPLE_RATE)
    if apply_noise_reduction:
        audio = _reduce_noise(audio, TARGET_SAMPLE_RATE)
    audio = _normalize(audio)

    out = output_path or input_path.with_suffix(".processed.wav")
    sf.write(str(out), audio, TARGET_SAMPLE_RATE)
    return out


def preprocess_bytes_to_wav(data: bytes, source_suffix: str) -> Path:
    """Write raw upload to temp file, preprocess, return processed WAV path."""
    from utils.storage import new_id
    from utils.paths import UPLOADS_DIR

    raw_id = new_id()
    raw_path = UPLOADS_DIR / f"{raw_id}_raw{source_suffix}"
    raw_path.write_bytes(data)
    processed = UPLOADS_DIR / f"{raw_id}_processed.wav"
    return preprocess_audio_file(raw_path, processed)
