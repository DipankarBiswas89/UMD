# Deployment guide

## Architecture

| Part | Host | Notes |
|------|------|--------|
| Frontend | Vercel | React + Vite |
| Backend | Render | Root dir: `BACKEND`, Python **3.11.9** (`runtime.txt`) |
| Database | Render Postgres | `DATABASE_URL` only — no localhost |

Voice cloning runs **in-process** on Render (Coqui XTTS v2). Local dev can use the optional `tts-service-python311` microservice on port 8001.

---

## 1. Render (backend)

**Settings**

- Root Directory: `BACKEND`
- Build: `pip install -r requirements.txt`
- Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`

**Required env vars**

```
DATABASE_URL=<Render Postgres Internal URL>
GROQ_API_KEY=<your key>
TTS_BACKEND=coqui
FRONTEND_URL=https://your-app.vercel.app
```

**Recommended**

```
LOG_LEVEL=INFO
WHISPER_MODEL=base
WHISPER_DEVICE=cpu
SKIP_WHISPER_WARMUP=false
```

**Speaker WAV:** commit `BACKEND/voices/voice.wav` or upload via the UI after deploy.

**Verify:** `GET https://<api>.onrender.com/health` → `database: true`, `xtts_ready: true`, `python: "3.11.9"`

See [BACKEND/RENDER_DEPLOY.md](BACKEND/RENDER_DEPLOY.md) for details.

---

## 2. Vercel (frontend)

**Root Directory:** `Frontend`

**Build:** `npm run build`  
**Output:** `dist`

**Environment variable (required in production)**

```
VITE_API_URL=https://your-backend.onrender.com
```

No trailing slash. Redeploy after setting this.

**Local dev:** leave `VITE_API_URL` unset; Vite proxies `/api` → `http://127.0.0.1:8000`.

---

## 3. Local development

### Option A — Python 3.11 monolith (matches Render)

```powershell
cd BACKEND
py -3.11 -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
# .env: DATABASE_URL, GROQ_API_KEY, TTS_BACKEND=coqui
.\.venv\Scripts\python -m uvicorn main:app --reload --port 8000
```

### Option B — Python 3.12 + TTS microservice

```powershell
# Terminal 1 — TTS (Python 3.11)
cd tts-service-python311
.\start_tts_service.ps1

# Terminal 2 — API (Python 3.12)
cd BACKEND
.\start_backend.ps1
# .env: TTS_BACKEND=microservice, TTS_SERVICE_URL=http://127.0.0.1:8001
```

```powershell
cd Frontend
npm install
npm run dev
```

---

## Pre-deploy checklist

- [ ] `DATABASE_URL` set on Render (not localhost)
- [ ] `FRONTEND_URL` matches Vercel URL (CORS)
- [ ] `VITE_API_URL` set on Vercel
- [ ] `voice.wav` in repo or uploaded post-deploy
- [ ] No `output_*.wav` in git (cached TTS outputs)
- [ ] `.env` never committed (secrets)
