# Quick script to restart the server
Write-Host "Stopping any running server processes..." -ForegroundColor Yellow

# Kill any Python processes running uvicorn (be careful!)
Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*uvicorn*" -or $_.CommandLine -like "*app.main*"
} | Stop-Process -Force -ErrorAction SilentlyContinue

Start-Sleep -Seconds 2

Write-Host "Starting server..." -ForegroundColor Green
Write-Host ""

# Activate venv and start server
& .\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

