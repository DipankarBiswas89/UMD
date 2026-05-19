# Render deployment checklist

## Render settings

| Setting | Value |
|---------|--------|
| Root Directory | `BACKEND` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| Runtime | `runtime.txt` → `python-3.11.9` |

## Environment variables (required)

```
DATABASE_URL=<Render Postgres Internal URL>
GROQ_API_KEY=<your key>
TTS_BACKEND=coqui
FRONTEND_URL=https://your-vercel-app.vercel.app
```

Render Postgres URL often starts with `postgresql://` — the app converts it to `postgresql+asyncpg://` automatically.

## Environment variables (recommended)

```
LOG_LEVEL=INFO
WHISPER_MODEL=base
WHISPER_DEVICE=cpu
TTS_USE_GPU=false
GROQ_MAX_TOKENS=128
```

## Voice sample on Render

Ephemeral disk: upload `voice.wav` via the UI after deploy, or bake into repo:

```
BACKEND/voices/voice.wav
```

## Verify after deploy

`GET https://your-api.onrender.com/health`

Expected:

```json
{
  "ok": true,
  "python": "3.11.9",
  "database": true,
  "coqui_installed": true,
  "xtts_ready": true
}
```

## Notes

- First deploy may take 15+ minutes (torch + TTS download).
- Free tier may OOM during XTTS load — use Starter plan or disable warmup (slower first request).
- Do **not** run `setup_database.py` CREATE DATABASE on Render — database already exists.
