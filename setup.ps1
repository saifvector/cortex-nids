# Universal Windows Automated Setup & Installation Script for Enterprise NIDS
$ErrorActionPreference = "Stop"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " CORTEX NIDS - AUTOMATED WINDOWS SETUP ENGINE" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

$ProjectRoot = $PSScriptRoot
Set-Location $ProjectRoot

# 1. Check Python installation and version (>= 3.11)
Write-Host "`n[1/7] Verifying Python 3.11+ Toolchain..." -ForegroundColor Yellow
try {
    $pyVerStr = & python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
    $pyMajor = [int]($pyVerStr.Split('.')[0])
    $pyMinor = [int]($pyVerStr.Split('.')[1])
    if ($pyMajor -lt 3 -or ($pyMajor -eq 3 -and $pyMinor -lt 11)) {
        Write-Error "Python version $pyVerStr is unsupported. Enterprise NIDS requires Python 3.11+."
        exit 1
    }
    Write-Host "  Found Python $pyVerStr (OK)" -ForegroundColor Green
} catch {
    Write-Error "Python 3 is not installed or not in PATH."
    exit 1
}

# 2. Check Git, Node.js, npm
Write-Host "`n[2/7] Checking Git, Node.js, and npm..." -ForegroundColor Yellow
foreach ($tool in @("git", "node", "npm")) {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
        Write-Error "Required tool '$tool' is not installed or not available in PATH."
        exit 1
    }
    Write-Host "  Found $tool (OK)" -ForegroundColor Green
}

# 3. Create Project Folder Structure
Write-Host "`n[3/7] Creating required storage directories..." -ForegroundColor Yellow
$folders = @("reports", "predictions", "logs", "temp", "uploads", "data/raw", "data/processed", "models/optimized")
foreach ($folder in $folders) {
    $path = Join-Path $ProjectRoot $folder
    if (-not (Test-Path $path)) {
        New-Item -ItemType Directory -Path $path -Force | Out-Null
        Write-Host "  Created directory: $folder" -ForegroundColor Gray
    }
}
Write-Host "  Directories verified (OK)" -ForegroundColor Green

# 4. Copy .env.example to .env if missing
Write-Host "`n[4/7] Verifying environment configuration (.env)..." -ForegroundColor Yellow
$envFile = Join-Path $ProjectRoot ".env"
$envExample = Join-Path $ProjectRoot ".env.example"
if (-not (Test-Path $envFile)) {
    if (Test-Path $envExample) {
        Copy-Item -Path $envExample -Destination $envFile
        Write-Host "  Copied .env.example to .env (OK)" -ForegroundColor Green
    } else {
        Write-Host "  Warning: .env.example not found." -ForegroundColor Yellow
    }
} else {
    Write-Host "  Existing .env configuration found (OK)" -ForegroundColor Green
}

# 5. Setup Python Virtual Environment & Install Dependencies
Write-Host "`n[5/7] Setting up Python Virtual Environment (.venv)..." -ForegroundColor Yellow
$venvPath = Join-Path $ProjectRoot ".venv"
$pythonVenv = Join-Path $venvPath "Scripts\python.exe"

if (-not (Test-Path $venvPath)) {
    & python -m venv .venv
    Write-Host "  Created Python virtual environment at .venv" -ForegroundColor Green
}

Write-Host "  Upgrading pip and installing Python requirements..." -ForegroundColor Yellow
& $pythonVenv -m pip install --upgrade pip --quiet
& $pythonVenv -m pip install -r requirements.txt --quiet
& $pythonVenv -m pip install -r requirements-dev.txt --quiet
Write-Host "  Python dependencies installed successfully (OK)" -ForegroundColor Green

# 6. Install Frontend Dependencies
Write-Host "`n[6/7] Installing Frontend React dependencies..." -ForegroundColor Yellow
$frontendDir = Join-Path $ProjectRoot "frontend"
if (Test-Path $frontendDir) {
    Set-Location $frontendDir
    & npm install --quiet
    Set-Location $ProjectRoot
    Write-Host "  Frontend npm dependencies installed (OK)" -ForegroundColor Green
}

# 7. Run Environment Validation Engine
Write-Host "`n[7/7] Executing Comprehensive Environment Validation Check..." -ForegroundColor Yellow
& $pythonVenv "scripts/check_environment.py"

Write-Host "`n==================================================" -ForegroundColor Cyan
Write-Host " LOCAL SETUP COMPLETE! HOW TO RUN THE PLATFORM:" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " 1. Run FastAPI Backend Server:" -ForegroundColor Green
Write-Host "    .venv\Scripts\python.exe scripts\run_api.py" -ForegroundColor Yellow
Write-Host ""
Write-Host " 2. Run React SOC Dashboard:" -ForegroundColor Green
Write-Host "    cd frontend; npm run dev" -ForegroundColor Yellow
Write-Host ""
Write-Host " 3. Or launch both automatically:" -ForegroundColor Green
Write-Host "    powershell -ExecutionPolicy Bypass -File scripts\start_local.ps1" -ForegroundColor Yellow
Write-Host "==================================================" -ForegroundColor Cyan
