# Moodwave Backend PowerShell Run Script
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$BackendDir = Join-Path $ProjectRoot "backend"
$VenvDir = Join-Path $BackendDir ".venv"

Write-Host "=== Starting Moodwave Backend Service ===" -ForegroundColor Cyan
Write-Host "Project Root: $ProjectRoot"
Write-Host "Backend Dir:  $BackendDir"

# Create virtual environment if it does not exist
if (-not (Test-Path $VenvDir)) {
    Write-Host "Creating virtual environment at $VenvDir..."
    python -m venv $VenvDir
}

# Activate virtual environment
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$VenvPip = Join-Path $VenvDir "Scripts\pip.exe"
$VenvUvicorn = Join-Path $VenvDir "Scripts\uvicorn.exe"

# Install or update requirements
Write-Host "Installing/verifying requirements from $BackendDir\requirements.txt..."
& $VenvPip install -r (Join-Path $BackendDir "requirements.txt")

# Run uvicorn from backend directory
Write-Host "Starting uvicorn on http://0.0.0.0:8000..."
Set-Location -Path $BackendDir
& $VenvUvicorn app.main:app --host 0.0.0.0 --port 8000
