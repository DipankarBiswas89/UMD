#!/usr/bin/env bash
# Railway / production build — Coqui TTS requires Python 3.11.x
set -euo pipefail

echo "Python: $(python --version)"
PY_MINOR=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
if [ "$PY_MINOR" != "3.11" ]; then
  echo "FATAL: TTS 0.22.0 needs Python 3.11.x, got $PY_MINOR"
  echo "Set Railway variable: PYTHON_VERSION=3.11.11"
  exit 1
fi

pip install --upgrade pip setuptools wheel
pip install "numpy>=1.24.0,<2.0"
pip install torch==2.5.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
python -c "import TTS; print('Coqui TTS', TTS.__version__)"
