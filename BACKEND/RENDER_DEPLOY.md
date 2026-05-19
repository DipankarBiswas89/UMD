# Render — API backend only (no Coqui)

Coqui XTTS runs on **Railway** (`tts-service-python311`). This service is FastAPI + Postgres + Whisper only.

## Render settings

| Setting | Value |
|---------|--------|
| Root Directory | `BACKEND` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn main:app --host 0.0.0.0 --port $PORT` |

No `runtime.txt` needed — use Render’s default Python 3.12+.

## Required environment variables

```
DATABASE_URL=<Render Postgres Internal URL>
GROQ_API_KEY=<your key>
TTS_BACKEND=microservice
TTS_SERVICE_URL=https://<your-railway-tts>.up.railway.app
FRONTEND_URL=https://your-app.vercel.app
```

`TTS_SERVICE_URL` must be the public Railway URL (no trailing slash).

## Verify

`GET https://<api>.onrender.com/health`

```json
{
  "ok": true,
  "database": true,
  "tts_microservice_healthy": true,
  "coqui_installed": false
}
```

`coqui_installed: false` is **expected** on Render.

## Speaker WAV

Commit `BACKEND/voices/voice.wav` or upload via UI. On startup the API syncs it to Railway TTS.

See [../DEPLOY.md](../DEPLOY.md) and [../tts-service-python311/RAILWAY_DEPLOY.md](../tts-service-python311/RAILWAY_DEPLOY.md).
