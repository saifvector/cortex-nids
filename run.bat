@echo off
REM Windows runner script for NIDS pipeline
cd /d "%~dp0"

if not exist .venv (
    echo [ERROR] Virtual environment ^(.venv^) not found.
    echo Please run 'scripts\setup_env.bat' first.
    exit /b 1
)

call .venv\Scripts\activate.bat
python scripts\run_pipeline.py %*
call deactivate
