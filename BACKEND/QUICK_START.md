# Quick Start Guide - Voice Assistant with Custom Voice

## ✅ Setup Complete!

Your system is now configured to use Python 3.11 with Coqui TTS for voice cloning.

## 🚀 Starting the Backend

### Option 1: Using PowerShell (Recommended)
```powershell
cd BACKEND
.\start_backend.ps1
```

### Option 2: Using Command Prompt
```cmd
cd BACKEND
start_backend.bat
```

### Option 3: Manual Start
```powershell
cd BACKEND
.\project_311\Scripts\Activate.ps1
python -m uvicorn main:app --reload
```

## 🎤 Your Voice Configuration

- **Voice Sample**: `BACKEND/voices/voice.wav` ✅
- **TTS Backend**: Coqui TTS (Python 3.11) ✅
- **Voice Cloning**: Enabled ✅

## 📋 What Was Set Up

1. ✅ Python 3.11 virtual environment (`project_311`)
2. ✅ Coqui TTS installed and working
3. ✅ All dependencies installed (FastAPI, Uvicorn, SQLAlchemy, etc.)
4. ✅ `.env` file configured with `TTS_BACKEND=coqui`
5. ✅ Startup scripts created (`start_backend.ps1` and `start_backend.bat`)
6. ✅ Cleaned up unnecessary files (Python 3.12 project, duplicate venvs, old audio files)

## 🧪 Testing Your Setup

1. **Start the backend** (see above)

2. **Check voice status**:
   ```powershell
   curl http://localhost:8000/voice-status
   ```
   Should show:
   ```json
   {
     "voice_sample": "BACKEND/voices/voice.wav",
     "tts_backend": "coqui"
   }
   ```

3. **Test with a question**:
   ```powershell
   curl "http://localhost:8000/ask-and-speak?question=Hello, this is a test"
   ```

4. **Or use the frontend**:
   ```powershell
   cd Frontend
   npm run dev
   ```
   Then open `http://localhost:5173` in your browser

## 🎯 Important Notes

- **Always use Python 3.11** for this project (Coqui TTS doesn't support Python 3.12)
- Your voice sample (`voice.wav`) is already in place
- The backend will automatically use your custom voice for all responses
- Generated audio files are saved in `BACKEND/voices/output_*.wav`

## 🔧 Troubleshooting

### "Coqui TTS not found"
```powershell
cd BACKEND
.\project_311\Scripts\pip.exe install TTS
```

### "Voice not being used"
- Check that `TTS_BACKEND=coqui` is in `BACKEND/.env`
- Verify `voice.wav` exists in `BACKEND/voices/`
- Restart the backend server

### "Python version error"
- Make sure you're using the Python 3.11 virtual environment
- Activate it: `.\project_311\Scripts\Activate.ps1`
- Check version: `python --version` (should show 3.11.x)

## 📁 Project Structure

```
Final Project/
├── BACKEND/
│   ├── project_311/          # Python 3.11 virtual environment
│   ├── voices/
│   │   └── voice.wav         # Your trained voice sample
│   ├── main.py               # FastAPI application
│   ├── tts_service.py        # TTS service with Coqui TTS
│   ├── .env                  # Environment variables
│   ├── start_backend.ps1     # PowerShell startup script
│   └── start_backend.bat     # Batch startup script
└── Frontend/                 # React frontend
```

## 🎉 You're All Set!

Your voice assistant is ready to use your custom trained voice. Just start the backend and frontend, and start chatting!
