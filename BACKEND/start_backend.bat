@echo off
REM Batch script to start the backend with Python 3.11 and Coqui TTS
REM This ensures your custom voice will be used

echo === Starting Voice Assistant Backend ===
echo.

REM Check if we're in the BACKEND directory
if not exist "main.py" (
    echo ERROR: Please run this script from the BACKEND directory
    exit /b 1
)

REM Check if Python 3.11 virtual environment exists
if not exist "project_311\Scripts\python.exe" (
    echo ERROR: Python 3.11 virtual environment not found!
    echo Please run: setup_coqui_env.ps1
    exit /b 1
)

REM Activate the Python 3.11 virtual environment
echo Activating Python 3.11 virtual environment...
call project_311\Scripts\activate.bat

REM Check if voice sample exists
if exist "voices\voice.wav" (
    echo [OK] Voice sample found: voices\voice.wav
) else (
    echo [WARNING] No voice sample found. Upload one via the frontend or API.
)

echo.
echo Starting FastAPI server...
echo Backend will be available at: http://localhost:8000
echo API docs at: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start the server
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
