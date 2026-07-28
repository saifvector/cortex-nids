@echo off
REM Windows setup script for NIDS environment
echo ==================================================
echo Setting up Network Intrusion Detection System Environment
echo ==================================================

cd /d "%~dp0\.."

REM 1. Check Python installation
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python was not found on your path. Please install Python 3.12+ and try again.
    exit /b 1
)

REM 2. Create virtual environment
if not exist .venv (
    echo [INFO] Creating Python virtual environment in .venv...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        exit /b 1
    )
) else (
    echo [INFO] Virtual environment .venv already exists.
)

REM 3. Activate environment and install requirements
echo [INFO] Activating virtual environment...
call .venv\Scripts\activate.bat

echo [INFO] Upgrading pip...
python -m pip install --upgrade pip

echo [INFO] Installing requirements from requirements.txt...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    exit /b 1
)

REM 4. Copy .env.example to .env if not exists
if not exist .env (
    echo [INFO] Creating local configuration file .env from template...
    copy .env.example .env >nul
) else (
    echo [INFO] File .env already exists, skipping copying.
)

echo ==================================================
echo Environment Setup Completed Successfully!
echo You can run the application using 'run.bat'
echo ==================================================
pause
