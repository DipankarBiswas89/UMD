# Real-Time AI Voice Assistant — Setup

## Project layout

```
Final Project/
├── BACKEND/                 # FastAPI server
│   ├── main.py              # App entry + legacy endpoints
│   ├── api/
│   │   ├── chat_service.py  # Groq AI responses
│   │   └── routes/
│   │       └── voice_assistant.py  # REST + WebSocket
│   ├── utils/
│   │   ├── audio_preprocess.py   # Noise reduction + normalize
│   │   ├── whisper_service.py    # faster-whisper STT
│   │   ├── storage.py
│   │   ├── recording_pipeline.py # Retraining queue
│   │   └── paths.py
│   ├── uploads/             # User mic recordings
│   ├── generated_audio/     # XTTS output WAVs
│   ├── models/              # Whisper model cache
│   ├── voices/              # Speaker WAV / .pth model
│   ├── tts_service.py       # Coqui XTTS v2
│   └── requirements.txt
├── Frontend/                # React + Vite UI
│   └── src/
│       ├── components/VoiceAssistant.jsx
│       ├── hooks/
│       └── api/voiceApi.js
```

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/record` | Save browser recording |
| POST | `/transcribe` | Whisper STT (file or `recording_id`) |
| POST | `/generate-response` | Groq chat reply |
| POST | `/generate-voice` | XTTS cloned speech |
| GET | `/audio/{audio_id}` | Play generated WAV |
| POST | `/voice-turn` | Full pipeline in one call |
| WS | `/ws/voice` | Real-time JSON pipeline |
| GET | `/training-queue` | Samples queued for Colab retrain |

Frontend calls these via `/api/*` (Vite proxy).

## Backend setup

1. **Python 3.11** recommended (Coqui XTTS requires Python &lt; 3.12).

2. Create venv and install:

```powershell
cd BACKEND
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install TTS torch torchaudio
```

3. Copy environment file:

```powershell
copy .env.example .env
```

Edit `.env` and set `GROQ_API_KEY` and `DATABASE_URL`.

4. Place your **speaker WAV** in `BACKEND/voices/` or upload from the UI.

5. Set `TTS_BACKEND=coqui` in `.env` for voice cloning.

6. Run server:

```powershell
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

First run downloads Whisper (`WHISPER_MODEL=base` by default) and may take a few minutes.

## Frontend setup

```powershell
cd Frontend
npm install
npm run dev
```

Open http://localhost:5173

## Voice flow

1. User taps mic → `MediaRecorder` captures WebM.
2. `POST /record` → preprocess (denoise, normalize) → stored in `uploads/`.
3. `POST /voice-turn` (or stepwise APIs): Whisper → Groq → XTTS.
4. Frontend plays `GET /api/audio/{id}` with play/pause/stop.

Clean recordings with transcripts are copied to `uploads/training_queue/` for future Colab fine-tuning.

## Environment variables

See `BACKEND/.env.example` for `GROQ_API_KEY`, `WHISPER_MODEL`, `TTS_BACKEND`, etc.

## Bonus features included

- WebSocket `/ws/voice` (send base64 audio or `recording_id`)
- Interrupt button stops TTS playback
- faster-whisper VAD during transcription
- Multilingual XTTS via `language` field on `/generate-voice`
