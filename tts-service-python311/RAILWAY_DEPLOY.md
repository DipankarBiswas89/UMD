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

## Health checks

| Path | Purpose |
|------|---------|
| `/health` | **Liveness** — returns 200 as soon as the server starts (Railway uses this) |
| `/health/ready` | **Readiness** — 200 only after XTTS weights are loaded (may take 5–15 min on CPU) |

## After deploy

1. `GET /health` → should be **200** quickly with `"status": "loading"`
2. Wait until `GET /health/ready` → **200** with `"model_loaded": true`
3. Then point Render `TTS_SERVICE_URL` at this service
3. Copy URL into Render backend:

```
TTS_SERVICE_URL=https://<service>.up.railway.app
TTS_BACKEND=microservice
```

## Speaker sample

On first voice request, Render backend uploads `voice.wav` to Railway via `/speakers/upload`. You can also place `speaker.wav` in Railway `speakers/` if using persistent volume.

## Notes

- **Healthcheck fix:** `/health` responds immediately; XTTS loads in the background. Use `/health/ready` to confirm cloning works.
- First model load may take **5–15 minutes** on CPU after deploy (watch Railway logs).
- Use at least **2–4 GB RAM** — XTTS OOM during load shows `status: failed` on `/health`.
- If deploy still fails, check **Deploy Logs** (not just build) for Python tracebacks.
- `build.sh` enforces Python 3.11 — required for `TTS==0.22.0`.
