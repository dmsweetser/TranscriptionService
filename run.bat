@echo off
REM === TranscriptionService – Windows Run Script ===
REM Usage: run.bat

setlocal enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies if not present
if not exist requirements.txt (
    echo requirements.txt not found. Please run install.bat first.
    pause
    exit /b
)

pip install -r requirements.txt --quiet 2>nul || goto run

:run
REM Run with Gunicorn for production
gunicorn -c gunicorn.conf.py app:app
pause
