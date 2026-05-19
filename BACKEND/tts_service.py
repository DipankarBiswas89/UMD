"""
TTS facade: in-process Coqui (Render/Python 3.11) -> external microservice -> Edge TTS fallback.
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

VOICE_DIR = Path(__file__).parent / "voices"
VOICE_DIR.mkdir(exist_ok=True)

TTS_BACKEND = os.getenv("TTS_BACKEND", "auto")
_GENERATED_NAME_PREFIXES = ("output_", "test_output", "generated_")


def is_valid_voice_sample_name(filename: str) -> bool:
    name = Path(filename).name.lower()
    return not any(name.startswith(p) for p in _GENERATED_NAME_PREFIXES)


def _use_local_coqui() -> bool:
    if TTS_BACKEND == "edge-tts":
        return False
    if TTS_BACKEND in ("coqui", "local"):
        return True
    if os.getenv("RENDER") or os.getenv("USE_LOCAL_COQUI", "").lower() in ("1", "true", "yes"):
        return True
    if TTS_BACKEND == "auto":
        from utils.coqui_local import is_coqui_installed

        return is_coqui_installed()
    if TTS_BACKEND == "microservice":
        return os.getenv("TTS_FORCE_LOCAL", "").lower() in ("1", "true", "yes")
    return False


class TTSService:
    def __init__(self):
        self.voice_model_path: Path | None = None
        self.voice_sample_path: Path | None = None
        self.edge_voice_name = os.getenv("EDGE_TTS_VOICE", "en-US-JennyNeural")
        self._edge_voice_checked = False
        self._edge_voice_lock = asyncio.Lock()
        self._tts_service_available: bool | None = None
        self._local_coqui_ready = False
        self._load_voice()

    def _load_voice(self) -> None:
        voice_files = [f for f in VOICE_DIR.glob("*") if f.is_file()]
        model_file = None
        sample_candidates: list[Path] = []

        for file in voice_files:
            if not is_valid_voice_sample_name(file.name):
                continue
            if file.suffix == ".pth":
                model_file = file
                break
            if file.suffix == ".onnx":
                model_file = file
            elif file.suffix in (".wav", ".mp3", ".flac"):
                sample_candidates.append(file)

        if model_file:
            self.voice_model_path = model_file
            logger.info("Found voice model: %s", model_file.name)
        elif sample_candidates:

            def _priority(p: Path) -> tuple[int, str]:
                n = p.name.lower()
                if n in ("voice.wav", "speaker.wav"):
                    return (0, n)
                if n.startswith("voice") or n.startswith("speaker"):
                    return (1, n)
                return (2, n)

            sample_candidates.sort(key=_priority)
            self.voice_sample_path = sample_candidates[0]
            logger.info("Found voice sample: %s", self.voice_sample_path.name)
        else:
            logger.warning("No voice sample in voices/ — upload speaker WAV for cloning")

    async def check_tts_service(self) -> bool:
        if TTS_BACKEND == "edge-tts":
            return False
        try:
            from services.tts_client import health_check

            data = await health_check()
            ok = bool(data.get("ok"))
            self._tts_service_available = ok
            return ok
        except Exception as exc:
            logger.warning("TTS microservice unreachable: %s", exc)
            self._tts_service_available = False
            return False

    async def warmup_coqui(self) -> None:
        """Warm up in-process XTTS on Render, or ping external TTS microservice."""
        if _use_local_coqui():
            from utils.coqui_local import is_coqui_installed, load_model_sync

            if not is_coqui_installed():
                logger.error("TTS package not installed — check requirements.txt and Python 3.11.9")
                self._local_coqui_ready = False
                return
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, load_model_sync)
                self._local_coqui_ready = True
                logger.info("XTTS initialized successfully (in-process)")
            except Exception as exc:
                self._local_coqui_ready = False
                logger.error("XTTS initialization failed: %s", exc)
            return

        if await self.check_tts_service():
            logger.info("TTS microservice is healthy")
        else:
            logger.warning(
                "TTS microservice unavailable at %s",
                os.getenv("TTS_SERVICE_URL", "http://127.0.0.1:8001"),
            )

    async def sync_speaker_to_microservice(self) -> None:
        if _use_local_coqui() or not self.voice_sample_path:
            return
        try:
            from services.tts_client import upload_speaker

            await upload_speaker(self.voice_sample_path)
            logger.info("Synced speaker to TTS microservice: %s", self.voice_sample_path.name)
        except Exception as exc:
            logger.warning("Speaker sync failed: %s", exc)

    async def _generate_local_coqui(self, text: str, output_path: Path) -> Path:
        from utils.coqui_local import synthesize_to_file

        if not self.voice_sample_path:
            raise RuntimeError("No speaker WAV — upload voice sample for cloning")

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: synthesize_to_file(
                text,
                self.voice_sample_path,
                output_path,
                os.getenv("TTS_LANGUAGE", "en"),
            ),
        )

    async def generate_speech(self, text: str, output_path: Optional[Path] = None) -> Path:
        started = time.perf_counter()
        if not output_path:
            output_path = VOICE_DIR / f"output_{hash(text) % 10000}.wav"

        if _use_local_coqui() and self._local_coqui_ready:
            try:
                await self._generate_local_coqui(text, output_path)
                logger.info("TTS local Coqui in %.0f ms", (time.perf_counter() - started) * 1000)
                return output_path
            except Exception as exc:
                logger.error("Local Coqui failed: %s", exc)
                if TTS_BACKEND in ("coqui", "local"):
                    raise RuntimeError(f"Voice cloning failed: {exc}") from exc

        tts_up = self._tts_service_available or await self.check_tts_service()
        if tts_up and TTS_BACKEND != "edge-tts":
            try:
                from services.tts_client import generate_voice_to_path

                await generate_voice_to_path(
                    text,
                    output_path,
                    self.voice_sample_path,
                    language=os.getenv("TTS_LANGUAGE", "en"),
                )
                logger.info("TTS microservice in %.0f ms", (time.perf_counter() - started) * 1000)
                return output_path
            except Exception as exc:
                logger.error("TTS microservice failed: %s", exc)
                if TTS_BACKEND in ("microservice", "coqui") and not _use_local_coqui():
                    raise RuntimeError(f"Voice cloning failed: {exc}") from exc

        logger.warning("Using Edge TTS fallback (no voice clone)")
        await self._generate_with_edge_tts(text, output_path)
        return output_path

    async def _generate_with_edge_tts(self, text: str, output_path: Path) -> None:
        import edge_tts

        try:
            communicate = edge_tts.Communicate(text, self.edge_voice_name)
            await communicate.save(str(output_path))
            return
        except Exception:
            pass

        async with self._edge_voice_lock:
            if not self._edge_voice_checked:
                voices = await edge_tts.list_voices()
                voice = next((v for v in voices if v["Locale"].startswith("en")), None)
                if voice:
                    self.edge_voice_name = voice["Name"]
                self._edge_voice_checked = True

        communicate = edge_tts.Communicate(text, self.edge_voice_name)
        await communicate.save(str(output_path))

    def set_voice_sample(self, file_path: Path) -> None:
        if not is_valid_voice_sample_name(file_path.name):
            raise ValueError(f"'{file_path.name}' is not a valid speaker sample name")
        self.voice_sample_path = file_path

    def set_voice_model(self, file_path: Path) -> None:
        self.voice_model_path = file_path


_tts_service: TTSService | None = None


def get_tts_service() -> TTSService:
    global _tts_service
    if _tts_service is None:
        _tts_service = TTSService()
    return _tts_service
