@echo off
setlocal
title CORTEX NIDS - Public Online Share Tunnel

echo.
echo ======================================================================
echo    CORTEX NIDS - PUBLIC ONLINE SHARE TUNNEL (ANY LAPTOP / DEVICE)
echo ======================================================================
echo.
echo [*] Checking prerequisites...
where npx >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] npx is not found! Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

echo [*] Starting instant secure HTTPS tunnel for port 3000...
echo.
echo ======================================================================
echo   A public HTTPS URL will appear below (e.g., https://....loca.lt)
echo   You can share this link with ANYONE on ANY laptop or phone anywhere!
echo ======================================================================
echo.
npx --yes localtunnel --port 3000

