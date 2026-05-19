# Start main backend (Python 3.12) - voice cloning via TTS microservice on :8001
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$Port = if ($env:BACKEND_PORT) { [int]$env:BACKEND_PORT } else { 8000 }

Write-Host "=== Voice Assistant Main Backend (Python 3.12) ===" -ForegroundColor Cyan
Write-Host "Uses .venv (not project_311). TTS microservice: ..\tts-service-python311" -ForegroundColor Gray
Write-Host ""

function Get-ListenerPid($port) {
    $line = netstat -ano | Select-String ":\s*$port\s+.*LISTENING" | Select-Object -First 1
    if (-not $line) { return $null }
    if ($line -match '\s+(\d+)\s*$') { return [int]$Matches[1] }
    return $null
}

$existing = Get-ListenerPid $Port
if ($existing) {
    $proc = Get-Process -Id $existing -ErrorAction SilentlyContinue
    $name = if ($proc) { $proc.ProcessName } else { "unknown" }
    Write-Host "Port $Port is in use by PID $existing ($name)." -ForegroundColor Yellow
    if ($name -eq "python" -or $name -eq "python3") {
        Write-Host "Stopping previous backend on port $Port..." -ForegroundColor Yellow
        Stop-Process -Id $existing -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
    } else {
        Write-Host "ERROR: Free port $Port or set `$env:BACKEND_PORT to another value (e.g. 8080)." -ForegroundColor Red
        exit 1
    }
}

$python = $null
foreach ($cmd in @("py -3.12", "python")) {
    try {
        $v = Invoke-Expression "$cmd --version 2>&1"
        if ($v -match "3\.12") { $python = $cmd; break }
    } catch { }
}
if (-not $python) {
    Write-Host "WARNING: Python 3.12 not found; using default python." -ForegroundColor Yellow
    $python = "python"
}

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    Write-Host "Creating .venv with $python..."
    Invoke-Expression "$python -m venv .venv"
    .\.venv\Scripts\pip install -r requirements.txt
}

$envFile = ".\.env"
if (Test-Path $envFile) {
    $envContent = Get-Content $envFile -Raw
    if ($envContent -notmatch "TTS_SERVICE_URL") {
        Add-Content $envFile "`nTTS_SERVICE_URL=http://127.0.0.1:8001"
        Write-Host "Added TTS_SERVICE_URL to .env" -ForegroundColor Green
    }
} else {
    Copy-Item ".\.env.example" $envFile
    Write-Host "Created .env from .env.example" -ForegroundColor Green
}

Write-Host "Starting http://127.0.0.1:$Port" -ForegroundColor Green
Write-Host "(Deactivate project_311 if active - this server uses BACKEND\.venv only)" -ForegroundColor Gray
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port $Port
