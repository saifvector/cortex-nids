@echo off
setlocal EnableDelayedExpansion

title CORTEX NIDS - Service Shutdown
cd /d "%~dp0"

echo.
echo ======================================================================
echo    CORTEX NIDS - PLATFORM SHUTDOWN CONTROLLER
echo ======================================================================
echo [*] Terminating only CORTEX NIDS backend and frontend processes...
echo.

:: 1. Terminate Backend process on port 8000
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$pids = (Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue).OwningProcess | Select-Object -Unique;" ^
    "if ($pids) {" ^
    "    foreach ($p in $pids) {" ^
    "        try { Stop-Process -Id $p -Force -ErrorAction Stop; Write-Host (' [STOPPED] Terminated FastAPI Backend (PID ' + $p + ')') -ForegroundColor Green } catch { Write-Host (' [WARN] Could not stop PID ' + $p + ': ' + $_) -ForegroundColor Yellow }" ^
    "    }" ^
    "} else {" ^
    "    Write-Host ' [INFO] Backend is not currently listening on port 8000.' -ForegroundColor DarkGray" ^
    "}"

:: 2. Terminate Frontend process on port 3000
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$pids = (Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue).OwningProcess | Select-Object -Unique;" ^
    "if ($pids) {" ^
    "    foreach ($p in $pids) {" ^
    "        try { Stop-Process -Id $p -Force -ErrorAction Stop; Write-Host (' [STOPPED] Terminated React/Vite Frontend (PID ' + $p + ')') -ForegroundColor Green } catch { Write-Host (' [WARN] Could not stop PID ' + $p + ': ' + $_) -ForegroundColor Yellow }" ^
    "    }" ^
    "} else {" ^
    "    Write-Host ' [INFO] Frontend is not currently listening on port 3000.' -ForegroundColor DarkGray" ^
    "}"

:: 3. Terminate background CMD wrapper windows matching project window titles
taskkill /FI "WINDOWTITLE eq CORTEX_NIDS_BACKEND*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq CORTEX_NIDS_FRONTEND*" /T /F >nul 2>&1

:: 4. Verify Port Deallocation
ping -n 2 127.0.0.1 >nul

set "PORT_8000_BUSY=0"
set "PORT_3000_BUSY=0"

for /f %%p in ('powershell -NoProfile -Command "(Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue).Count"') do (
    if %%p gtr 0 set "PORT_8000_BUSY=1"
)

for /f %%p in ('powershell -NoProfile -Command "(Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue).Count"') do (
    if %%p gtr 0 set "PORT_3000_BUSY=1"
)

echo.
if !PORT_8000_BUSY! equ 0 if !PORT_3000_BUSY! equ 0 (
    echo ======================================================================
    echo   [SUCCESS] All CORTEX NIDS services have been shut down cleanly!
    echo   Ports 8000 and 3000 are completely freed.
    echo ======================================================================
) else (
    echo [WARN] Some ports may still have lingering connections.
    if !PORT_8000_BUSY! equ 1 echo  - Port 8000 is still busy.
    if !PORT_3000_BUSY! equ 1 echo  - Port 3000 is still busy.
)
echo.

:: Brief pause before exit
ping -n 3 127.0.0.1 >nul
exit /b 0
