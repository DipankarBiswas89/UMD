# Voice Setup Guide

This guide explains how to upload and use your custom voice sample/model that you trained in Google Colab.

## Supported Formats

### Voice Samples (for voice cloning)
- `.wav` - Recommended format
- `.mp3` - Supported
- `.flac` - Supported

### Voice Models
- `.pth` - Coqui TTS model file
- `.onnx` - Piper TTS model file

## How to Upload Your Voice

### Method 1: Using the Web Interface

1. **Start the application**:
   ```bash
   # Backend (in BACKEND directory)
   cd BACKEND
   python main.py
   # or
   uvicorn main:app --reload
   
   # Frontend (in Frontend directory)
   cd Frontend
   npm run dev
   ```

2. **Open the application** in your browser (usually `http://localhost:5173`)

3. **Click on "📤 Upload Voice Sample/Model"** button

4. **Select your voice file** (.wav, .mp3, .flac, .pth, or .onnx)

5. **Wait for upload confirmation** - You'll see a success message

6. **Check the voice status** - The status will show which voice file is currently active

### Method 2: Direct File Upload (API)

You can also upload using curl or Postman:

```bash
curl -X POST "http://localhost:8000/upload-voice" \
  -F "file=@/path/to/your/voice.wav"
```

## Setting Up TTS Backend

The system supports multiple TTS backends. Configure which one to use by setting the `TTS_BACKEND` environment variable in your `.env` file:

### Option 1: Coqui TTS (Recommended for voice cloning)

1. **Install Coqui TTS**:
   ```bash
   pip install TTS
   ```

2. **Set in .env**:
   ```
   TTS_BACKEND=coqui
   ```

3. **Upload your voice sample** (.wav, .mp3, or .flac file)

   Coqui TTS will use your voice sample for voice cloning. The system will automatically use XTTS-v2 model for voice cloning.

### Option 2: Piper TTS

1. **Install Piper TTS**:
   ```bash
   # Download piper-tts binary or install via package manager
   # See: https://github.com/rhasspy/piper
   ```

2. **Set in .env**:
   ```
   TTS_BACKEND=piper
   ```

3. **Upload your .onnx model file**

### Option 3: Edge TTS (Fallback - No custom voice)

If you don't have a custom voice, the system will fall back to Edge TTS:

1. **Install Edge TTS**:
   ```bash
   pip install edge-tts
   ```

2. **Set in .env**:
   ```
   TTS_BACKEND=edge-tts
   ```

**Note**: Edge TTS doesn't support custom voices, so this is only a fallback option.

## Using Your Trained Voice from Google Colab

If you trained a voice in Google Colab, you likely have one of these:

### Scenario 1: You have a voice sample (.wav file)

1. **Download your voice sample** from Google Colab
2. **Upload it** using the web interface or API
3. **The system will use it** for voice cloning with Coqui TTS

### Scenario 2: You have a trained model (.pth file)

1. **Download your model file** from Google Colab
2. **Upload it** using the web interface or API
3. **The system will load your custom model** for TTS generation

### Scenario 3: You have multiple files

If you have multiple files (model + config), you may need to:
1. **Upload the main model file** (.pth)
2. **Place config files** in the `BACKEND/voices/` directory manually
3. **Restart the backend** to load the model

## File Locations

- **Uploaded files are stored in**: `BACKEND/voices/`
- **Generated audio files**: `BACKEND/voices/output_*.wav`
- **Audio files are served at**: `http://localhost:8000/audio/`

## Troubleshooting

### Voice not working?

1. **Check voice status**:
   ```bash
   curl http://localhost:8000/voice-status
   ```

2. **Check backend logs** for errors

3. **Verify file format** - Make sure your file is in a supported format

4. **Check TTS backend** - Ensure the correct TTS library is installed:
   ```bash
   pip install TTS  # For Coqui TTS
   # or
   pip install edge-tts  # For Edge TTS fallback
   ```

### Audio not playing in frontend?

1. **Check browser console** for errors
2. **Verify audio URL** is accessible: `http://localhost:8000/audio/filename.wav`
3. **Check CORS settings** if accessing from different origin

### Model not loading?

1. **Check file permissions** - Ensure the backend can read files in `BACKEND/voices/`
2. **Check model compatibility** - Ensure the model format matches the TTS backend
3. **Check logs** for specific error messages

## Example: Complete Setup

```bash
# 1. Install Coqui TTS
pip install TTS

# 2. Set environment variable (in BACKEND/.env)
echo "TTS_BACKEND=coqui" >> BACKEND/.env

# 3. Start backend
cd BACKEND
python main.py

# 4. In another terminal, start frontend
cd Frontend
npm run dev

# 5. Open browser to http://localhost:5173
# 6. Upload your voice.wav file
# 7. Start chatting - responses will use your custom voice!
```

## API Endpoints

- `POST /upload-voice` - Upload voice sample/model
- `GET /voice-status` - Get current voice configuration
- `GET /audio/{filename}` - Access generated audio files
- `GET /ask-and-speak?question=...` - Get response with audio URL

## Notes

- **Voice samples** work best with Coqui TTS (XTTS-v2) for voice cloning
- **Model files** (.pth) are loaded directly if available
- **Generated audio** is cached in the voices directory
- **File size limits**: Large model files may take time to upload and load

