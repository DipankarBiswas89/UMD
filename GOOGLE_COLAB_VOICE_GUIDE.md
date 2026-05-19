# Using Your Google Colab Trained Voice

## Overview
This guide explains how to use the voice you trained in Google Colab with this application.

## Step 1: Download Your Trained Voice from Google Colab

### What Files Do You Have?

Depending on what you trained in Google Colab, you might have:

1. **Voice Sample File** (`.wav`, `.mp3`, or `.flac`)
   - A recording of your voice
   - Used for voice cloning
   - Usually 5-30 seconds long

2. **Trained Model File** (`.pth` for Coqui TTS)
   - A complete trained model
   - Larger file (usually 100MB+)
   - Contains the voice characteristics
   

3. **Model Checkpoint** (`.pth` or `.ckpt`)
   - Training checkpoint
   - Can be used to continue training or generate speech

### How to Download from Google Colab

**Method 1: Direct Download**
```python
# In Google Colab, run this to download your files:
from google.colab import files

# Download voice sample
files.download('path/to/your/voice.wav')

# Download model (if you have one)
files.download('path/to/your/model.pth')
```

**Method 2: Save to Google Drive**
```python
# In Google Colab, save to Drive first:
import shutil

# Copy to Drive
shutil.copy('path/to/voice.wav', '/content/drive/MyDrive/voice.wav')
shutil.copy('path/to/model.pth', '/content/drive/MyDrive/model.pth')

# Then download from Google Drive
```

**Method 3: Use Colab File Browser**
1. Click the folder icon (📁) in the left sidebar
2. Navigate to your files
3. Right-click → Download

## Step 2: Prepare Your Files

### Check What You Have

Look for these files in your Google Colab output:
- `voice.wav` or similar audio file
- `model.pth` or `checkpoint.pth` (if you trained a full model)
- `config.json` (model configuration, optional)

### File Requirements

**For Voice Cloning (Recommended):**
- **Voice Sample**: `.wav` file (best quality)
  - Duration: 5-30 seconds
  - Format: Mono or Stereo, 16kHz or higher
  - Clear speech, minimal background noise

**For Full Model:**
- **Model File**: `.pth` file
  - Complete trained model
  - Usually includes config files

## Step 3: Upload to This Application

### Option A: Using the Web Interface (Easiest)

1. **Start the application**:
   ```bash
   # Backend
   cd BACKEND
   # Prefer Python 3.11 env for voice cloning
   # If you already ran setup_coqui_env.ps1:
   #   .\project_311\Scripts\Activate.ps1
   # Otherwise (current env):
   python -m uvicorn main:app --reload
   
   # Frontend (new terminal)
   cd Frontend
   npm run dev
   ```

2. **Open the app**: Go to `http://localhost:5173`

3. **Click "📤 Upload Voice Sample/Model"**

4. **Select your file**:
   - If you have a voice sample: Upload `.wav`, `.mp3`, or `.flac`
   - If you have a model: Upload `.pth` file

5. **Wait for confirmation**: You'll see "✅ Voice sample uploaded successfully"

### Option B: Using API (Command Line)

```bash
# Upload voice sample
curl -X POST "http://localhost:8000/upload-voice" \
  -F "file=@/path/to/your/voice.wav"

# Upload model
curl -X POST "http://localhost:8000/upload-voice" \
  -F "file=@/path/to/your/model.pth"
```

### Option C: Manual Copy

1. Copy your file to: `BACKEND/voices/`
2. Name it something clear: `my_voice.wav` or `trained_model.pth`
3. Restart the backend server

## Step 4: Configure the System

### Check Your Python Version

```bash
python --version
```

**If Python 3.11 or lower:**
- ✅ You can use Coqui TTS with voice cloning
- Set in `BACKEND/.env`: `TTS_BACKEND=coqui`
- Install: `pip install TTS`

**If Python 3.12:**
- ⚠️ Coqui TTS doesn't work (requires Python < 3.12)
- You have two options:
  1. **Use Python 3.11** (recommended - run `BACKEND/setup_coqui_env.ps1`)
  2. **Use Edge TTS** (but it won't use your custom voice)

### Set Environment Variable

Create or edit `BACKEND/.env`:
```env
# Auto-detect (tries Coqui if a voice is present, else Edge TTS)
TTS_BACKEND=auto

# If running on Python 3.11 and want to force voice cloning:
# TTS_BACKEND=coqui

# If staying on Python 3.12 and accept no cloning:
# TTS_BACKEND=edge-tts
```

## Step 5: Test Your Voice

1. **Restart the backend server**

2. **Check voice status**:
   ```bash
   curl http://localhost:8000/voice-status
   ```
   
   Should show:
   ```json
   {
     "voice_sample": "BACKEND/voices/voice.wav",
     "voice_model": null,
     "tts_backend": "coqui"
   }
   ```

3. **Send a test message**:
   - Go to the frontend
   - Type: "Hello, this is a test"
   - Send
   - Listen to the response - it should use your voice!

## Common Google Colab Training Scenarios

### Scenario 1: You Trained with Coqui TTS XTTS-v2

**What you have:**
- Trained model files (`.pth`)
- Possibly voice samples used for training

**How to use:**
1. Download the `.pth` model file
2. Upload it to the application
3. The system will use it for voice cloning

**Example Colab code you might have used:**
```python
# In Google Colab
from TTS.api import TTS

# Train or use model
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
tts.tts_to_file(
    text="Hello",
    file_path="output.wav",
    speaker_wav="your_voice.wav"  # Your voice sample
)
```

### Scenario 2: You Trained a Custom Model

**What you have:**
- Model checkpoint (`.pth` or `.ckpt`)
- Config files (`config.json`)
- Voice samples

**How to use:**
1. Download the model file and config (if separate)
2. Upload model to: `BACKEND/voices/`
3. If config is separate, place it in the same directory
4. The system will load it automatically

### Scenario 3: You Only Have a Voice Sample

**What you have:**
- Just a `.wav` file of your voice

**How to use:**
1. Upload the `.wav` file
2. System will use it with Coqui TTS XTTS-v2 for voice cloning
3. No model training needed - XTTS-v2 does voice cloning on-the-fly

## Troubleshooting

### "Voice uploaded but not being used"

**Check:**
1. Python version: `python --version`
2. Coqui TTS installed: `pip list | findstr TTS`
3. Backend logs for errors
4. Voice file exists: `dir BACKEND\voices\`

**Solution:**
- If Python 3.12: Install Python 3.11 and use Coqui TTS
- See `BACKEND/INSTALL_COQUI_TTS.md` or run `BACKEND/setup_coqui_env.ps1`

### "Coqui TTS not installed"

```bash
# Install Coqui TTS (requires Python 3.11)
pip install TTS
```

### "Model file not loading"

**Check:**
1. File format: Should be `.pth` for Coqui TTS
2. File location: Should be in `BACKEND/voices/`
3. File permissions: Make sure readable

**Solution:**
- Try uploading via web interface instead of manual copy
- Check backend logs for specific error

### "Voice sounds different"

**Possible reasons:**
1. Using Edge TTS instead of Coqui TTS (no custom voice)
2. Voice sample quality too low
3. Model not fully trained

**Solution:**
- Make sure you're using Coqui TTS (`TTS_BACKEND=coqui`)
- Use a high-quality voice sample (16kHz+, clear audio)
- If using a model, ensure it's fully trained

## Quick Reference

### File Locations
- **Uploaded files**: `BACKEND/voices/`
- **Generated audio**: `BACKEND/voices/output_*.wav`
- **Config**: `BACKEND/.env`

### API Endpoints
- **Upload**: `POST /upload-voice`
- **Status**: `GET /voice-status`
- **Test**: `GET /ask-and-speak?question=test`

### Supported Formats
- **Voice samples**: `.wav` (best), `.mp3`, `.flac`
- **Models**: `.pth` (Coqui TTS), `.onnx` (Piper TTS)

## Next Steps

1. ✅ Download your voice/model from Google Colab
2. ✅ Upload it to the application
3. ✅ Configure Python 3.11 + Coqui TTS (if needed)
4. ✅ Test with a message
5. ✅ Enjoy your custom voice! 🎉

## Need Help?

Check these files:
- `BACKEND/INSTALL_COQUI_TTS.md` - Python 3.11 setup
- `VOICE_SETUP_GUIDE.md` - General voice setup
- `PYTHON_VERSION_NOTE.md` - Python version info

