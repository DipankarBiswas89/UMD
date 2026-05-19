# How to Use Your Custom Voice with Coqui TTS

## Problem
- You uploaded `voice.wav` but it's not being used
- Edge TTS (current backend) **does NOT support custom voice cloning**
- Coqui TTS supports voice cloning but requires Python < 3.12

## Solution: Install Python 3.11 and Coqui TTS

### Step 1: Install Python 3.11

1. Download Python 3.11 from: https://www.python.org/downloads/release/python-31111/
2. Install it (you can have both Python 3.11 and 3.12 installed)

### Step 2: Create a New Virtual Environment with Python 3.11

```bash
# Navigate to BACKEND directory
cd BACKEND

# Create virtual environment with Python 3.11
# Replace python3.11 with the path to your Python 3.11 installation if needed
python3.11 -m venv project_311

# Activate the virtual environment
# Windows PowerShell:
project_311\Scripts\Activate.ps1
# Windows CMD:
project_311\Scripts\activate.bat
# Linux/Mac:
source project_311/bin/activate
```

### Step 3: Install All Dependencies

```bash
pip install fastapi uvicorn httpx python-dotenv sqlalchemy psycopg2-binary asyncpg python-multipart TTS
```

### Step 4: Configure Backend

Add to `BACKEND/.env`:
```
TTS_BACKEND=coqui
```

### Step 5: Run the Server

```bash
python -m uvicorn main:app --reload
```

### Step 6: Upload Your Voice Again

1. Go to the frontend
2. Upload your `voice.wav` file again
3. Send a message
4. Your custom voice will now be used! 🎉

## Alternative: Quick Test

If you want to test if Coqui TTS works with your current Python version:

```bash
pip install TTS
python -c "from TTS.api import TTS; print('Coqui TTS works!')"
```

If this fails with a Python version error, you need Python 3.11.

## Verification

After setting up with Python 3.11:
1. Check logs - you should see: "Generated speech with Coqui TTS"
2. The voice should sound like your uploaded sample
3. Check `/voice-status` endpoint - it should show your voice sample

## Troubleshooting

**Error: "Coqui TTS not installed"**
- Make sure you're in the Python 3.11 virtual environment
- Run: `pip install TTS`

**Error: "Python version not supported"**
- Make sure you're using Python 3.11 (check with `python --version`)
- Create a new venv with Python 3.11

**Voice still not working**
- Make sure `voice.wav` is uploaded
- Check `BACKEND/voices/` directory has your file
- Restart the server after uploading

