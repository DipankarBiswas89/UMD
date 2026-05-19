# Microservice Architecture — AI Voice Assistant

## Overview

Coqui XTTS v2 **only runs on Python 3.11**. The main API stays on **Python 3.12**. Voice cloning is isolated in a dedicated TTS microservice.

```
┌─────────────┐     HTTP      ┌──────────────────────┐
│  Frontend   │ ────────────► │  Main Backend        │
│  React/Vite │   :5173→:8000 │  Python 3.12         │
│  (Frontend/)│               │  (BACKEND/)          │
└─────────────┘               └──────────┬───────────┘
                                         │ REST
                                         │ TTS_SERVICE_URL
                                         ▼
                              ┌──────────────────────┐
                              │  TTS Microservice    │
                              │  Python 3.11         │
                              │  (tts-service-       │
                              │   python311/) :8001  │
                              │  Coqui XTTS v2       │
                              └──────────────────────┘
```

## Folder map

| Path | Role | Python |
|------|------|--------|
| `Frontend/` | React UI (= `frontend/`) | Node |
| `BACKEND/` | Main API (= `backend-python312/`) | **3.12** |
| `tts-service-python311/` | Voice cloning only | **3.11** |

## Quick start (local)

### 1. TTS microservice (port 8001)

```powershell
cd tts-service-python311
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env

# Copy your speaker reference
copy ..\BACKEND\voices\voice.wav .\speakers\voice.wav

uvicorn main:app --host 0.0.0.0 --port 8001
```

First start downloads XTTS weights (~2GB). Wait for log: `TTS microservice ready`.

### 2. Main backend (port 8000)

```powershell
cd BACKEND
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
# Set GROQ_API_KEY, DATABASE_URL, TTS_SERVICE_URL=http://127.0.0.1:8001

uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### 3. Frontend

```powershell
cd Frontend
npm install
npm run dev
```

Open http://localhost:5173

## Docker (TTS only)

```powershell
docker compose up --build tts-service
```

TTS API: http://localhost:8001/docs

## API reference

### TTS microservice (`:8001`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health + model loaded |
| POST | `/generate-voice` | Form: `text`, `speaker_wav` or `speaker_file` |
| POST | `/generate-voice/json` | JSON body |
| GET | `/audio/{audio_id}` | Download WAV |
| POST | `/speakers/upload` | Store reference speaker |
| GET | `/speakers` | List speakers |

### Main backend (`:8000`)

Unchanged for the frontend (`/api/*` proxy):

- `POST /voice-turn` — full pipeline
- `POST /generate-voice` — delegates to TTS service
- `GET /audio/{id}` — serves cached output

## Environment

### Main backend (`BACKEND/.env`)

```env
TTS_BACKEND=microservice
TTS_SERVICE_URL=http://127.0.0.1:8001
TTS_REQUEST_TIMEOUT=300
GROQ_API_KEY=...
DATABASE_URL=...
```

### TTS service (`tts-service-python311/.env`)

```env
TTS_PORT=8001
TTS_USE_GPU=false
TTS_MODEL=tts_models/multilingual/multi-dataset/xtts_v2
```

## Production recommendations

1. **Run TTS on GPU** — set `TTS_USE_GPU=true` in Docker/env.
2. **Health checks** — main backend should fail fast if `/health` on TTS is down when `TTS_BACKEND=microservice`.
3. **Shared storage** — mount `speakers/` volume in Docker; sync uploads via `POST /speakers/upload`.
4. **Timeouts** — XTTS first request can take 60–120s; keep `TTS_REQUEST_TIMEOUT=300`.
5. **Scale TTS horizontally** — run multiple TTS replicas behind a load balancer; main backend is stateless for TTS.
6. **Do not install `TTS` in main backend** — keeps Python 3.12 deps clean.
7. **Cleanup** — TTS service auto-deletes generated WAVs older than `AUDIO_TTL_HOURS` (default 24h).

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Voice cloning failed | Start TTS service on :8001; check `TTS_SERVICE_URL` |
| No speaker found | Copy `voice.wav` to `tts-service-python311/speakers/` or upload via UI |
| transformers / BeamSearchScorer | Only in TTS venv — pin `transformers<4.47` |
| WebM mic 500 | Fixed in main backend via PyAV — ensure `av` installed |

## Migrating from monolith `project_311`

You no longer need `BACKEND/project_311` for the main server. Use:

- **BACKEND** → Python 3.12 + `TTS_SERVICE_URL`
- **tts-service-python311** → Python 3.11 + Coqui only
