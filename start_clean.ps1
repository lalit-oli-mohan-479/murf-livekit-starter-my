$ErrorActionPreference = "Stop"

function Test-CommandExists {
  param([string]$CommandName)
  return $null -ne (Get-Command $CommandName -ErrorAction SilentlyContinue)
}

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host " Cleaning up existing processes...      " -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# Force stop stale Python, Node, and LiveKit server processes to prevent conflicts
Stop-Process -Name python -Force -ErrorAction SilentlyContinue
Stop-Process -Name node -Force -ErrorAction SilentlyContinue
Stop-Process -Name livekit-server -Force -ErrorAction SilentlyContinue

Start-Sleep -Seconds 2

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

# Start LiveKit server
if (Test-Path "$repoRoot\livekit-server.exe") {
  Write-Host "Starting local livekit-server..." -ForegroundColor Green
  Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$repoRoot'; .\livekit-server.exe --dev"
} elseif (Test-CommandExists "livekit-server") {
  Write-Host "Starting livekit-server..." -ForegroundColor Green
  Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$repoRoot'; livekit-server --dev"
} else {
  Write-Warning "livekit-server executable not found. Skipping local LiveKit startup."
}

# Start backend Python agent
Write-Host "Starting backend agent (uv run)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$repoRoot\backend'; uv run python src/agent.py dev"

# Start frontend Next.js dev server
Write-Host "Starting frontend dev server (pnpm dev)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$repoRoot\frontend'; pnpm dev"

Write-Host "=========================================" -ForegroundColor Green
Write-Host " Stale processes cleaned & services run! " -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
