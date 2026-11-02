@echo off
setlocal EnableDelayedExpansion

:: Set console title and change to script directory
title CORTEX NIDS - Application Launcher
cd /d "%~dp0"

echo.
echo ======================================================================
echo    ____ ___  ____ _____ _______  __   _   _ ___ ____  ____  
echo   / ___/ _ \^|  _ \_   _^| ____\ \/ /  ^| \ ^| ^|_ _^|  _ \/ ___^| 
echo  ^| ^|  ^| ^| ^| ^| ^|_) ^|^| ^| ^|  _^|  \  /   ^|  \^| ^|^| ^|^| ^| ^| \___ \ 
echo  ^| ^|__^| ^|_^| ^|  _ ^< ^| ^| ^| ^|___ /  \   ^| ^|\  ^|^| ^|^| ^|_^| ^|___) ^|
echo   \____\___/^|_^| \_\^|_^| ^|_____/_/\_\  ^|_^| \_^|___^|____/^|____/ 
echo.
echo   CORTEX NIDS: AI-Based Bidirectional Network Intrusion Detection
echo ======================================================================
echo.

:: -------------------------------------------------------------------
:: 1. Pre-Flight Validation Checks
:: -------------------------------------------------------------------
echo [*] Running pre-flight system checks...

:: Check Python Virtual Environment
set "PYTHON_EXE="
set "VENV_ACTIVATE=%~dp0.venv\Scripts\activate.bat"

if exist "%~dp0.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
    echo  [OK] Found Python virtual environment: .venv
) else (
    where python >nul 2>&1
    if !errorlevel! equ 0 (
        set "PYTHON_EXE=python"
        echo  [WARN] Virtual environment '.venv' not found. Using system Python.
    ) else (
        echo.
        echo [ERROR] Python is not installed or not in PATH!
        echo Please install Python 3.10+ from https://www.python.org/downloads/
        echo and create the virtual environment using:
        echo   python -m venv .venv
        echo   .venv\Scripts\pip install -r requirements.txt
        echo.
        goto :ERROR_EXIT
    )
)

:: Check Node.js and npm
where node >nul 2>&1
if !errorlevel! neq 0 (
    echo.
    echo [ERROR] Node.js is not installed or not in PATH!
    echo Please install Node.js 18+ from https://nodejs.org/
    echo.
    goto :ERROR_EXIT
)
echo  [OK] Found Node.js:
node --version

where npm >nul 2>&1
if !errorlevel! neq 0 (
    echo.
    echo [ERROR] npm is not installed or not in PATH!
    echo Please install Node.js and npm from https://nodejs.org/
    echo.
    goto :ERROR_EXIT
)
echo  [OK] Found npm package manager

:: Check Frontend node_modules
if not exist "%~dp0frontend\node_modules" (
    echo.
    echo [ERROR] Frontend dependencies are missing in 'frontend\node_modules'!
    echo Please install dependencies first by running:
    echo   cd frontend
    echo   npm install
    echo.
    goto :ERROR_EXIT
)
echo  [OK] Found frontend dependencies in 'frontend\node_modules'

:: Check Backend Entry Point
if not exist "%~dp0scripts\run_api.py" (
    echo.
    echo [ERROR] Backend entry point 'scripts\run_api.py' not found!
    echo Make sure you are running launch.bat from the project root.
    echo.
    goto :ERROR_EXIT
)
echo  [OK] Found backend entry point: scripts\run_api.py

:: Check Trained Model
if not exist "%~dp0models\best_model.joblib" (
    echo  [WARN] Trained model artifact 'models\best_model.joblib' not detected.
    echo         Backend will operate using available fallback models.
) else (
    echo  [OK] Found production model artifact: models\best_model.joblib
)

echo.
echo ======================================================================
echo [*] Checking active ports and service status...
echo ======================================================================

:: -------------------------------------------------------------------
:: 2. Duplicate Instance Detection
:: -------------------------------------------------------------------
set "BACKEND_ALREADY_RUNNING=0"
set "FRONTEND_ALREADY_RUNNING=0"

for /f %%p in ('powershell -NoProfile -Command "(Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue).Count"') do (
    if %%p gtr 0 (
        set "BACKEND_ALREADY_RUNNING=1"
    )
)

for /f %%p in ('powershell -NoProfile -Command "(Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue).Count"') do (
    if %%p gtr 0 (
        set "FRONTEND_ALREADY_RUNNING=1"
    )
)

if !BACKEND_ALREADY_RUNNING! equ 1 (
    echo  [INFO] Port 8000 is already active. Reusing existing Backend service.
)

if !FRONTEND_ALREADY_RUNNING! equ 1 (
    echo  [INFO] Port 3000 is already active. Reusing existing Frontend service.
)

:: -------------------------------------------------------------------
:: 3. Spawn Services
:: -------------------------------------------------------------------
if !BACKEND_ALREADY_RUNNING! equ 0 (
    echo [*] Starting FastAPI Backend on http://127.0.0.1:8000 ...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%PYTHON_EXE%' -ArgumentList 'scripts\run_api.py --host 127.0.0.1 --port 8000' -WorkingDirectory '%~dp0' -WindowStyle Minimized"
)

if !FRONTEND_ALREADY_RUNNING! equ 0 (
    echo [*] Starting React/Vite Frontend on http://localhost:3000 ...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process cmd.exe -ArgumentList '/c npm run dev' -WorkingDirectory '%~dp0frontend' -WindowStyle Minimized"
)

echo.
echo [*] Waiting for services to initialize...

:: -------------------------------------------------------------------
:: 4. Health Check Polling
:: -------------------------------------------------------------------
set "BACKEND_READY=0"
for /l %%i in (1,1,30) do (
    if !BACKEND_READY! equ 0 (
        for /f %%s in ('powershell -NoProfile -Command "try { (Invoke-WebRequest -Uri 'http://127.0.0.1:8000/health' -UseBasicParsing -TimeoutSec 1).StatusCode } catch { 0 }"') do (
            if "%%s"=="200" (
                set "BACKEND_READY=1"
                echo  [OK] FastAPI Backend is healthy on attempt %%i.
            )
        )
        if !BACKEND_READY! equ 0 (
            ping -n 2 127.0.0.1 >nul
        )
    )
)

if !BACKEND_READY! equ 0 (
    echo.
    echo [ERROR] Backend service failed to become healthy within 30 seconds!
    echo Please check the 'CORTEX_NIDS_BACKEND' console window for error logs.
    echo You can also test manually by running:
    echo   call .venv\Scripts\activate.bat
    echo   python scripts\run_api.py --port 8000
    echo.
    goto :ERROR_EXIT
)

set "FRONTEND_READY=0"
for /l %%i in (1,1,30) do (
    if !FRONTEND_READY! equ 0 (
        for /f %%s in ('powershell -NoProfile -Command "try { (Invoke-WebRequest -Uri 'http://localhost:3000' -UseBasicParsing -TimeoutSec 1).StatusCode } catch { 0 }"') do (
            if "%%s"=="200" (
                set "FRONTEND_READY=1"
                echo  [OK] React/Vite Frontend is responsive on attempt %%i.
            )
        )
        if !FRONTEND_READY! equ 0 (
            ping -n 2 127.0.0.1 >nul
        )
    )
)

if !FRONTEND_READY! equ 0 (
    echo  [WARN] Frontend did not return HTTP 200 within 30s, but Vite is loading in background.
)

:: -------------------------------------------------------------------
:: 5. Success Screen & Launch Browser
:: -------------------------------------------------------------------
echo.
echo ======================================================================
echo   [SUCCESS] CORTEX NIDS PLATFORM IS FULLY OPERATIONAL!
echo ======================================================================
echo   SOC Dashboard   : http://localhost:3000
echo   FastAPI Backend : http://127.0.0.1:8000
echo   Swagger API Docs: http://127.0.0.1:8000/docs
echo   ReDoc Specs     : http://127.0.0.1:8000/redoc
echo   Health Check    : http://127.0.0.1:8000/health
echo ======================================================================
echo.
echo [*] Launching SOC Dashboard in your default web browser...
start "" "http://localhost:3000"

if /i "%~1"=="--test" (
    echo [*] Automated test mode detected. Exiting launcher cleanly while services remain active.
    exit /b 0
)

:: -------------------------------------------------------------------
:: 6. Interactive Process Monitor
:: -------------------------------------------------------------------
:MENU_LOOP
echo.
echo [COMMANDS]
echo   [S] Stop all CORTEX NIDS services now (runs stop.bat)
echo   [D] Open Swagger API Documentation in browser
echo   [R] Reload Dashboard in browser
echo   [Q] Quit this launcher window (services keep running in background)
echo.
set /p "USER_CHOICE=Select an option [S/D/R/Q] and press Enter: "

if /i "%USER_CHOICE%"=="S" (
    echo.
    call "%~dp0stop.bat"
    goto :EOF
)

if /i "%USER_CHOICE%"=="D" (
    echo [*] Opening API Docs...
    start "" "http://127.0.0.1:8000/docs"
    goto :MENU_LOOP
)

if /i "%USER_CHOICE%"=="R" (
    echo [*] Reloading Dashboard...
    start "" "http://localhost:3000"
    goto :MENU_LOOP
)

if /i "%USER_CHOICE%"=="Q" (
    echo.
    echo [*] Exiting launcher window. Backend and Frontend continue running.
    echo [*] Run 'stop.bat' whenever you want to shut down all services.
    ping -n 3 127.0.0.1 >nul
    goto :EOF
)

echo [!] Invalid choice. Please enter S, D, R, or Q.
goto :MENU_LOOP

:ERROR_EXIT
echo.
echo ======================================================================
echo   STARTUP FAILED: Review the error messages above.
echo   Press any key to close this window...
echo ======================================================================
pause >nul
exit /b 1
