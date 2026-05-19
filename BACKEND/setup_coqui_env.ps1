# Requires: Python 3.11 installed and accessible as python3.11 or py -3.11
# This script creates a Python 3.11 virtualenv and installs dependencies
#
# Usage (PowerShell):
#   cd BACKEND
#   .\setup_coqui_env.ps1

Write-Host "=== Setting up Python 3.11 virtual environment for Coqui TTS ===" -ForegroundColor Cyan

# Locate Python 3.11
$pythonCandidates = @(
    "python3.11",
    "py -3.11",
    "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
    "$env:ProgramFiles\Python311\python.exe",
    "$env:ProgramFiles(x86)\Python311\python.exe"
)

$python311 = $null
foreach ($cmd in $pythonCandidates) {
    try {
        $version = & $cmd --version 2>$null
        if ($LASTEXITCODE -eq 0 -and $version -like "*3.11*") {
            $python311 = $cmd
            break
        }
    } catch {
        # ignore and continue
    }
}

if (-not $python311) {
    Write-Host "ERROR: Python 3.11 not found. Install Python 3.11 first." -ForegroundColor Red
    Write-Host "Download: https://www.python.org/downloads/release/python-31111/"
    exit 1
}

Write-Host "Using Python: $python311" -ForegroundColor Green

# Create virtual environment
if (Test-Path ".\project_311") {
    Write-Host "Virtual environment 'project_311' already exists. Skipping creation." -ForegroundColor Yellow
} else {
    & $python311 -m venv project_311
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to create virtual environment." -ForegroundColor Red
        exit 1
    }
    Write-Host "Created virtual environment: project_311" -ForegroundColor Green
}

# Activate and install dependencies
Write-Host "Activating environment and installing dependencies..." -ForegroundColor Cyan
$envPath = ".\project_311\Scripts\Activate.ps1"
if (-not (Test-Path $envPath)) {
    Write-Host "ERROR: Activate script not found at $envPath" -ForegroundColor Red
    exit 1
}

& $envPath
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to activate virtual environment." -ForegroundColor Red
    exit 1
}

Write-Host "Installing requirements.txt + Coqui TTS (this may take several minutes)..." -ForegroundColor Cyan
pip install --upgrade pip
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: requirements.txt installation failed." -ForegroundColor Red
    exit 1
}
pip install TTS torch torchaudio
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Coqui TTS installation failed." -ForegroundColor Red
    exit 1
}

# Coqui TTS 0.22 requires transformers 4.x (5.x breaks BeamSearchScorer)
pip install "transformers>=4.33.0,<4.47.0" "numpy>=1.24,<2.0" "torch>=2.1,<2.6"
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Pinning transformers/numpy for Coqui failed." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=== Setup complete ===" -ForegroundColor Green
Write-Host "To run the backend with your custom voice (Coqui TTS + voice cloning):" -ForegroundColor Yellow
Write-Host "1) Activate env:    .\project_311\Scripts\Activate.ps1"
Write-Host "2) Set backend:     setx TTS_BACKEND coqui  (or add to BACKEND\\.env)"
Write-Host "3) Start server:    python -m uvicorn main:app --reload"
Write-Host ""
Write-Host "If you haven't yet, upload your voice via the frontend or POST /upload-voice." -ForegroundColor Yellow


