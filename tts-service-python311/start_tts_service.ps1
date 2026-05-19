# Start TTS microservice (Python 3.11 + Coqui XTTS v2) on port 8001
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$Port = 8001

function Get-ListenerPid($port) {
    $line = netstat -ano | Select-String ":\s*$port\s+.*LISTENING" | Select-Object -First 1
    if (-not $line) { return $null }
    if ($line -match '\s+(\d+)\s*$') { return [int]$Matches[1] }
    return $null
}

$existing = Get-ListenerPid $Port
if ($existing) {
    $proc = Get-Process -Id $existing -ErrorAction SilentlyContinue
    if ($proc -and $proc.ProcessName -match "python") {
        Write-Host "Stopping previous process on port $Port (PID $existing)..." -ForegroundColor Yellow
        Stop-Process -Id $existing -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
    }
}

# Prefer existing Coqui venv in BACKEND, else local .venv
$PythonExe = $null
$candidates = @(
    "..\BACKEND\project_311\Scripts\python.exe",
    ".\.venv\Scripts\python.exe"
)
foreach ($c in $candidates) {
    if (Test-Path $c) { $PythonExe = (Resolve-Path $c).Path; break }
}

if (-not $PythonExe) {
    Write-Host "Creating Python 3.11 venv (first time - may take 10+ min to install Coqui)..." -ForegroundColor Cyan
    py -3.11 -m venv .venv
    $PythonExe = (Resolve-Path ".\.venv\Scripts\python.exe").Path
    & $PythonExe -m pip install --upgrade pip
    & $PythonExe -m pip install -r requirements.txt
}

if (-not (Test-Path ".\speakers\voice.wav")) {
    $src = "..\BACKEND\voices\voice.wav"
    if (Test-Path $src) {
        Copy-Item $src ".\speakers\voice.wav" -Force
        Write-Host "Copied speaker: voice.wav" -ForegroundColor Green
    } else {
        Write-Host "WARNING: No voice.wav in speakers/ - upload one for cloning" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "=== TTS Microservice (XTTS v2) ===" -ForegroundColor Cyan
Write-Host "URL: http://127.0.0.1:$Port" -ForegroundColor Green
Write-Host "Docs: http://127.0.0.1:$Port/docs" -ForegroundColor Gray
Write-Host "First start loads the model - wait for 'TTS microservice ready'" -ForegroundColor Yellow
Write-Host "Keep this window open while using the voice assistant." -ForegroundColor Yellow
Write-Host ""

& $PythonExe -m uvicorn main:app --host 127.0.0.1 --port $Port
