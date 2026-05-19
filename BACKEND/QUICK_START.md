# Quick start

Full deployment: see [../DEPLOY.md](../DEPLOY.md).

## Local (fastest)

1. PostgreSQL running with `DATABASE_URL` in `BACKEND/.env`
2. `cd BACKEND` → `.\start_backend.ps1`
3. `cd Frontend` → `npm install` → `npm run dev`
4. Open http://localhost:5173

**Voice cloning locally (Python 3.12):** start `tts-service-python311` on port 8001, set `TTS_BACKEND=microservice` in `.env`.

**Voice cloning locally (Python 3.11):** use full `requirements.txt` and `TTS_BACKEND=coqui` (same as Render).

## Verify

```powershell
cd BACKEND
python test_db_connection.py
curl http://127.0.0.1:8000/health
```
