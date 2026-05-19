# Railway — Coqui XTTS microservice (Python 3.11)

Deploy **only** the `tts-service-python311` folder (not the whole monorepo root unless you set root directory).

## Railway settings

| Setting | Value |
|---------|--------|
| Root Directory | `tts-service-python311` (if repo root is parent) |
| Build Command | `bash build.sh` |
| Start Command | `uvicorn main:app --host 0.0.0.0 --port $PORT` |

Or use **Dockerfile** (recommended for reproducibility):

| Setting | Value |
|---------|--------|
| Builder | Dockerfile |
| Dockerfile path | `tts-service-python311/Dockerfile` |

## Environment variables

```
PYTHON_VERSION=3.11.11
TTS_USE_GPU=false
TTS_LANGUAGE=en
LOG_LEVEL=INFO
```

Railway sets `PORT` automatically — do not hardcode 8001 in production.

## After deploy

1. Open `https://<service>.up.railway.app/health`
2. Expect: `"xtts_ready": true`
3. Copy URL into Render backend:

```
TTS_SERVICE_URL=https://<service>.up.railway.app
TTS_BACKEND=microservice
```

## Speaker sample

On first voice request, Render backend uploads `voice.wav` to Railway via `/speakers/upload`. You can also place `speaker.wav` in Railway `speakers/` if using persistent volume.

## Notes

- First deploy may take 15+ minutes (torch + XTTS model download).
- Use at least 2 GB RAM plan if builds OOM.
- `build.sh` enforces Python 3.11 — required for `TTS==0.22.0`.
