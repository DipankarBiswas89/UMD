# Deployment guide (3 services)

| Service | Platform | Folder | Python | Coqui TTS |
|---------|----------|--------|--------|-----------|
| Frontend | Vercel | `Frontend` | — | — |
| API backend | Render | `BACKEND` | 3.12+ (default) | **No** |
| Voice cloning | Railway | `tts-service-python311` | **3.11** | **Yes** |

```
Browser (Vercel) → Render API → Railway TTS (XTTS v2)
                      ↓
                 Render Postgres
```

---

## 1. Railway — TTS microservice (deploy first)

See [tts-service-python311/RAILWAY_DEPLOY.md](tts-service-python311/RAILWAY_DEPLOY.md).

Copy the public URL, e.g. `https://your-tts.up.railway.app`.

Test: `GET https://your-tts.up.railway.app/health` → `"xtts_ready": true`

---

## 2. Render — API backend

**Root:** `BACKEND`  
**Build:** `pip install -r requirements.txt`  
**Start:** `uvicorn main:app --host 0.0.0.0 --port $PORT`

```
DATABASE_URL=<Render Postgres Internal URL>
GROQ_API_KEY=<key>
TTS_BACKEND=microservice
TTS_SERVICE_URL=https://your-tts.up.railway.app
FRONTEND_URL=https://your-app.vercel.app
```

Details: [BACKEND/RENDER_DEPLOY.md](BACKEND/RENDER_DEPLOY.md)

---

## 3. Vercel — frontend

**Root:** `Frontend`  
**Build:** `npm run build`  
**Output:** `dist`

```
VITE_API_URL=https://your-api.onrender.com
```

---

## Local development

```powershell
# Terminal 1 — TTS (Python 3.11)
cd tts-service-python311
.\start_tts_service.ps1

# Terminal 2 — API
cd BACKEND
# .env: TTS_BACKEND=microservice, TTS_SERVICE_URL=http://127.0.0.1:8001
.\start_backend.ps1

# Terminal 3 — Frontend
cd Frontend
npm run dev
```

---

## Checklist

- [ ] Railway TTS healthy (`/health`)
- [ ] Render `TTS_SERVICE_URL` points to Railway
- [ ] Render `DATABASE_URL` set (not localhost)
- [ ] Vercel `VITE_API_URL` points to Render
- [ ] `voice.wav` on Render backend (syncs to Railway on startup)
