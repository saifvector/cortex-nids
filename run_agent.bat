@echo off
setlocal
title CORTEX NIDS - Endpoint Telemetry Agent
cd /d "%~dp0"

echo ======================================================================
echo    CORTEX NIDS: Real-Time Laptop Endpoint Telemetry Agent
echo ======================================================================
echo.
echo [*] Streaming live laptop network sockets to CORTEX NIDS Cloud...
echo [*] Monitoring applications: Brave, Chrome, Edge, AnyDesk, etc.
echo.

if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" scripts\run_agent.py %*
) else (
    python scripts\run_agent.py %*
)

pause
