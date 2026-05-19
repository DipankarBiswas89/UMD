# Start API backend (no Coqui — use tts-service-python311 on :8001 or Railway)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$Port = if ($env:BACKEND_PORT) { [int]$env:BACKEND_PORT } else { 8000 }

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
        Stop-Process -Id $existing -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
    }
}

$pythonCmd = "python"
foreach ($cmd in @("py -3.12", "py -3.11", "python")) {
    try {
        $v = Invoke-Expression "$cmd --version 2>&1" | Out-String
        if ($v -match "Python 3") { $pythonCmd = $cmd; break }
    } catch { }
}

Write-Host "=== API Backend (no Coqui in requirements.txt) ===" -ForegroundColor Cyan
Write-Host "Start tts-service-python311 first, then set TTS_SERVICE_URL in .env" -ForegroundColor Gray

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    Invoke-Expression "$pythonCmd -m venv .venv"
    .\.venv\Scripts\pip install -r requirements.txt
}

if (-not (Test-Path ".\.env")) {
    Copy-Item ".\.env.example" ".\.env"
}

Write-Host "http://127.0.0.1:$Port" -ForegroundColor Green
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port $Port
