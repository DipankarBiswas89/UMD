# Quick start

Architecture: [../DEPLOY.md](../DEPLOY.md)

```powershell
# 1) TTS microservice (Python 3.11)
cd tts-service-python311
.\start_tts_service.ps1

# 2) API (any Python 3.11+)
cd BACKEND
# .env: TTS_BACKEND=microservice, TTS_SERVICE_URL=http://127.0.0.1:8001
.\start_backend.ps1

# 3) Frontend
cd Frontend
npm run dev
```
