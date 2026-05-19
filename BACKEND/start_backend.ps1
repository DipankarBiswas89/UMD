# Start main backend API
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
    $name = if ($proc) { $proc.ProcessName } else { "unknown" }
    Write-Host "Port $Port in use by PID $existing ($name)." -ForegroundColor Yellow
    if ($name -match "python") {
        Stop-Process -Id $existing -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
    } else {
        Write-Host "Free port $Port or set `$env:BACKEND_PORT" -ForegroundColor Red
        exit 1
    }
}

$pythonCmd = $null
$useCoreOnly = $false
foreach ($spec in @(
    @{ Cmd = "py -3.11"; Core = $false },
    @{ Cmd = "py -3.12"; Core = $true },
    @{ Cmd = "python"; Core = $true }
)) {
    try {
        $v = Invoke-Expression "$($spec.Cmd) --version 2>&1" | Out-String
        if ($v -match "Python 3") {
            $pythonCmd = $spec.Cmd
            $useCoreOnly = $spec.Core
            break
        }
    } catch { }
}
if (-not $pythonCmd) {
    Write-Host "Python not found." -ForegroundColor Red
    exit 1
}

$reqFile = if ($useCoreOnly) { "requirements-core.txt" } else { "requirements.txt" }
Write-Host "=== Voice Assistant Backend ===" -ForegroundColor Cyan
if ($useCoreOnly) {
    Write-Host "Python 3.12 detected — using requirements-core.txt + TTS microservice (:8001)" -ForegroundColor Gray
    Write-Host "Start tts-service-python311 first, set TTS_BACKEND=microservice in .env" -ForegroundColor Gray
} else {
    Write-Host "Python 3.11 — full stack (matches Render deploy)" -ForegroundColor Gray
}

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    Write-Host "Creating .venv with $pythonCmd ..."
    Invoke-Expression "$pythonCmd -m venv .venv"
    .\.venv\Scripts\pip install -r $reqFile
}

if (-not (Test-Path ".\.env")) {
    Copy-Item ".\.env.example" ".\.env"
    Write-Host "Created .env from .env.example" -ForegroundColor Green
}

Write-Host "Starting http://127.0.0.1:$Port" -ForegroundColor Green
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port $Port
