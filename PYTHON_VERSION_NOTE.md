# Python Version Compatibility Note

## Important: Coqui TTS Limitation

**Coqui TTS does not support Python 3.12** (requires Python < 3.12).

If you're using Python 3.12 (which you are), the system will automatically use **Edge TTS** as the TTS backend.

## Current Status

- ✅ **Edge TTS**: Installed and working (supports Python 3.12)
- ❌ **Coqui TTS**: Not compatible with Python 3.12

## Options for Custom Voice

### Option 1: Use Edge TTS (Current Setup)
- ✅ Works with Python 3.12
- ✅ No installation issues
- ❌ **Does NOT support custom voice cloning**
- Uses Microsoft Edge TTS voices (high quality, but not your custom voice)

### Option 2: Use Python 3.11 for Coqui TTS
If you want to use your custom voice with Coqui TTS:

1. **Install Python 3.11** (separate from Python 3.12)
2. **Create a new virtual environment** with Python 3.11:
   ```bash
   python3.11 -m venv venv_311
   venv_311\Scripts\activate  # Windows
   ```
3. **Install dependencies**:
   ```bash
   pip install TTS fastapi uvicorn httpx python-dotenv sqlalchemy psycopg2-binary asyncpg python-multipart
   ```
4. **Run the backend** with Python 3.11

### Option 3: Wait for Coqui TTS Update
Coqui TTS may add Python 3.12 support in future releases. Check their GitHub for updates.

## Current Behavior

With Python 3.12:
- ✅ Voice upload works (files are saved)
- ✅ Audio generation works (using Edge TTS)
- ⚠️ Custom voice cloning is NOT available (Edge TTS limitation)
- ✅ System falls back gracefully to Edge TTS

## Testing

Try sending a message now - it should work with Edge TTS, but won't use your custom voice sample.

To use your custom voice, you'll need to either:
1. Switch to Python 3.11 and use Coqui TTS
2. Wait for Coqui TTS to support Python 3.12
3. Use a different TTS solution that supports Python 3.12 and voice cloning

