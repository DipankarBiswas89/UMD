# Coqui XTTS requires Python 3.11
FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libsndfile1 \
    ffmpeg \
    espeak-ng \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt build.sh ./
RUN pip install --upgrade pip setuptools wheel && \
    bash build.sh

COPY . .

RUN mkdir -p speakers generated

EXPOSE 8001

ENV PORT=8001

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=5 \
    CMD python -c "import os,urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\",\"8001\")}/health', timeout=5)" || exit 1

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8001}"]
