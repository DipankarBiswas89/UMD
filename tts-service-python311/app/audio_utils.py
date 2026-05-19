"""Audio helpers and cleanup."""
from __future__ import annotations

import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)


def apply_noise_reduction_placeholder(audio_path: Path) -> Path:
    """
    Placeholder for future noise-reduction pipeline before/after synthesis.
    Returns the same path unchanged.
    """
    logger.debug("Noise reduction placeholder (no-op): %s", audio_path.name)
    return audio_path


def cleanup_old_files(directory: Path, max_age_seconds: int) -> int:
    """Remove generated files older than max_age_seconds."""
    if not directory.exists():
        return 0
    now = time.time()
    removed = 0
    for path in directory.glob("*.wav"):
        try:
            if now - path.stat().st_mtime > max_age_seconds:
                path.unlink(missing_ok=True)
                removed += 1
        except OSError as exc:
            logger.warning("Could not remove %s: %s", path, exc)
    return removed
