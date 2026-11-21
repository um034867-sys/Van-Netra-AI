$ROOT = $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($ROOT)) {
    $ROOT = "."
}
$BACKEND = "$ROOT\backend"
$PYTHON  = "$ROOT\.venv\Scripts\python.exe"
$YOLO_DIR = "$ROOT\.tmp\ultralytics"

Write-Host ""
Write-Host "========================================="
Write-Host "        VAN NETRA  —  STARTUP"
Write-Host "========================================="
Write-Host ""

# Ensure local Ultralytics config dir exists (avoids AppData permission issues)
if (!(Test-Path $YOLO_DIR)) {
    New-Item -ItemType Directory -Path $YOLO_DIR -Force | Out-Null
}

# Check Python
if (!(Test-Path $PYTHON)) {
    Write-Host "ERROR: Python virtual environment not found at $PYTHON"
    pause
    exit
}

# Check backend
if (!(Test-Path "$BACKEND\main.py")) {
    Write-Host "ERROR: backend/main.py not found."
    pause
    exit
}

# Check frontend
if (!(Test-Path "$ROOT\package.json")) {
    Write-Host "ERROR: package.json not found."
    pause
    exit
}

Write-Host "[1/3] Seeding database (first run only, skips if already seeded)..."
$env:YOLO_CONFIG_DIR = $YOLO_DIR
& $PYTHON "$BACKEND\seed_demo_data.py"

Write-Host ""
Write-Host "[2/3] Starting Van Netra Backend..."

Start-Process powershell -ArgumentList `
    "-NoExit", `
    "-Command", `
    "`$env:YOLO_CONFIG_DIR='$YOLO_DIR'; Set-Location '$ROOT'; & '$PYTHON' -m uvicorn backend.main:app --host 127.0.0.1 --port 8001 --reload"

Start-Sleep -Seconds 5

Write-Host "[3/3] Starting Van Netra Frontend..."

Start-Process powershell -ArgumentList `
    "-NoExit", `
    "-Command", `
    "Set-Location '$ROOT'; npm run dev -- --port 5174 --strictPort"

Start-Sleep -Seconds 6

Write-Host "Opening Van Netra..."
Start-Process "http://localhost:5174"

Write-Host ""
Write-Host "========================================="
Write-Host "        VAN NETRA  —  RUNNING"
Write-Host "========================================="
Write-Host ""
Write-Host "Frontend : http://localhost:5174"
Write-Host "Backend  : http://127.0.0.1:8001"
Write-Host "API Docs : http://127.0.0.1:8001/docs"
Write-Host ""
Write-Host "Keep the two terminal windows open."
Write-Host ""
pause



