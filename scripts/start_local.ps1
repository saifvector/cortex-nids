# ============================================================
# Cortex NIDS Platform - Local Stack Launcher (No Docker)
# Starts FastAPI backend + React frontend in parallel
# ============================================================

$ProjectRoot = Split-Path -Parent $PSScriptRoot

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  CORTEX NIDS - LOCAL STACK LAUNCHER" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# --- Validate Python venv ---
$pythonExe = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    Write-Error "Python venv not found at $pythonExe. Run: python -m venv .venv && .venv\Scripts\pip install -r requirements.txt"
    exit 1
}

# --- Validate Node/npm ---
if (-not (Get-Command "npm" -ErrorAction SilentlyContinue)) {
    Write-Error "npm is not installed or not in PATH. Install Node.js from https://nodejs.org"
    exit 1
}

Write-Host "[1/2] Starting FastAPI Backend on http://localhost:8000 ..." -ForegroundColor Yellow
$backendJob = Start-Job -ScriptBlock {
    param($root, $python)
    Set-Location $root
    & $python "scripts\run_api.py" --host "0.0.0.0" --port 8000
} -ArgumentList $ProjectRoot, $pythonExe

Write-Host "[2/2] Starting React Frontend on http://localhost:5173 ..." -ForegroundColor Yellow
$frontendJob = Start-Job -ScriptBlock {
    param($root)
    Set-Location "$root\frontend"
    npm run dev
} -ArgumentList $ProjectRoot

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "  CORTEX NIDS PLATFORM IS STARTING..." -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host "  SOC Dashboard  : http://localhost:5173" -ForegroundColor Green
Write-Host "  FastAPI Backend : http://localhost:8000" -ForegroundColor Green
Write-Host "  Swagger API Docs: http://localhost:8000/docs" -ForegroundColor Green
Write-Host "  ReDoc Docs      : http://localhost:8000/redoc" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop all services." -ForegroundColor Gray

# Stream output from both jobs until Ctrl+C
try {
    while ($true) {
        # Print backend output
        Receive-Job $backendJob | ForEach-Object { Write-Host "[BACKEND] $_" -ForegroundColor DarkCyan }
        # Print frontend output
        Receive-Job $frontendJob | ForEach-Object { Write-Host "[FRONTEND] $_" -ForegroundColor DarkMagenta }

        # Check if jobs crashed
        if ($backendJob.State -eq "Failed") {
            Write-Host "[ERROR] Backend job failed!" -ForegroundColor Red
            Receive-Job $backendJob -ErrorAction SilentlyContinue
            break
        }
        if ($frontendJob.State -eq "Failed") {
            Write-Host "[ERROR] Frontend job failed!" -ForegroundColor Red
            Receive-Job $frontendJob -ErrorAction SilentlyContinue
            break
        }

        Start-Sleep -Milliseconds 500
    }
} finally {
    Write-Host "`nStopping all services..." -ForegroundColor Yellow
    Stop-Job $backendJob, $frontendJob -ErrorAction SilentlyContinue
    Remove-Job $backendJob, $frontendJob -ErrorAction SilentlyContinue
    Write-Host "All services stopped." -ForegroundColor Gray
}
