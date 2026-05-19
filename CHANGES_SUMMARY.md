# Changes Summary - Custom Voice Integration

## Overview
The application has been updated to use your custom trained voice instead of TTS_API_KEY. The system now supports uploading voice samples/models and generating speech using your custom voice.

## What Changed

### Backend Changes (`BACKEND/main.py`)

1. **Removed ElevenLabs dependency** - No longer uses TTS_API_KEY
2. **Added TTS Service** - New `tts_service.py` module for custom voice generation
3. **Added Voice Upload Endpoint** - `POST /upload-voice` for uploading voice files
4. **Added Voice Status Endpoint** - `GET /voice-status` to check current voice configuration
5. **Modified `/ask-and-speak` endpoint** - Now generates audio using custom voice and returns `audio_url`
6. **Added Audio Serving** - Static file serving for generated audio files at `/audio/`

### Frontend Changes (`Frontend/src/App.jsx`)

1. **Removed browser TTS** - No longer uses `SpeechSynthesisUtterance` as primary method
2. **Added Audio Playback** - Plays custom voice audio from backend
3. **Added Voice Upload UI** - Button and file input for uploading voice samples/models
4. **Added Voice Status Display** - Shows current voice configuration
5. **Fallback to Browser TTS** - Falls back to browser TTS if audio generation fails

### New Files

1. **`BACKEND/tts_service.py`** - TTS service supporting multiple backends:
   - Coqui TTS (XTTS-v2) - Recommended for voice cloning
   - Piper TTS - For .onnx models
   - Edge TTS - Fallback option

2. **`BACKEND/voices/`** - Directory for storing:
   - Uploaded voice samples (.wav, .mp3, .flac)
   - Uploaded voice models (.pth, .onnx)
   - Generated audio files

3. **`VOICE_SETUP_GUIDE.md`** - Complete guide for setting up and using custom voices

## How to Use

### Step 1: Install TTS Library

Choose one of these options:

**Option A: Coqui TTS (Recommended)**
```bash
pip install TTS
```

**Option B: Edge TTS (Fallback)**
```bash
pip install edge-tts
```

### Step 2: Configure Backend

Add to `BACKEND/.env`:
```
TTS_BACKEND=coqui
```

### Step 3: Start the Application

```bash
# Terminal 1 - Backend
cd BACKEND
python main.py

# Terminal 2 - Frontend
cd Frontend
npm run dev
```

### Step 4: Upload Your Voice

1. Open `http://localhost:5173` in your browser
2. Click "📤 Upload Voice Sample/Model"
3. Select your voice file:
   - **Voice sample**: `.wav`, `.mp3`, or `.flac` file from Google Colab
   - **Voice model**: `.pth` file (Coqui TTS model) or `.onnx` file (Piper TTS model)
4. Wait for upload confirmation
5. Check the voice status indicator

### Step 5: Test

1. Type a message or use voice input
2. Send the message
3. The response will use your custom voice!

## Supported Voice Formats

### Voice Samples (for voice cloning)
- `.wav` - Recommended, best quality
- `.mp3` - Supported
- `.flac` - Supported

### Voice Models
- `.pth` - Coqui TTS model (from Google Colab training)
- `.onnx` - Piper TTS model

## API Endpoints

### Upload Voice
```
POST /upload-voice
Content-Type: multipart/form-data
Body: file=<voice_file>
```

### Get Voice Status
```
GET /voice-status
Response: {
  "voice_model": "path/to/model.pth",
  "voice_sample": "path/to/sample.wav",
  "tts_backend": "coqui",
  "voices_directory": "BACKEND/voices"
}
```

### Ask and Speak (Modified)
```
GET /ask-and-speak?question=your_question
Response: {
  "answer": "Response text",
  "audio_url": "/audio/output_1234.wav"
}
```

## File Structure

```
BACKEND/
├── main.py              # Updated with TTS integration
├── tts_service.py       # NEW - TTS service module
├── voices/              # NEW - Voice files directory
│   ├── your_voice.wav  # Uploaded voice sample
│   └── output_*.wav    # Generated audio files
└── .env                 # Add TTS_BACKEND=coqui

Frontend/
└── src/
    └── App.jsx          # Updated with voice upload UI
```

## Troubleshooting

### Voice not working?
1. Check `BACKEND/voices/` directory exists
2. Verify voice file was uploaded successfully
3. Check backend logs for TTS errors
4. Ensure TTS library is installed: `pip install TTS`

### Audio not playing?
1. Check browser console for errors
2. Verify audio URL is accessible: `http://localhost:8000/audio/filename.wav`
3. Check CORS settings if accessing from different origin

### Model not loading?
1. Check file format matches TTS backend
2. Verify file permissions
3. Check backend logs for specific errors

## Migration Notes

- **No breaking changes** - Existing functionality still works
- **Browser TTS fallback** - If custom voice fails, falls back to browser TTS
- **Backward compatible** - Old API responses still work, just without `audio_url`

## Next Steps

1. Upload your voice sample/model from Google Colab
2. Test with a few messages
3. Adjust TTS settings if needed (in `tts_service.py`)
4. Enjoy your custom voice assistant!

