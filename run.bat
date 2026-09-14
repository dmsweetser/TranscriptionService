@echo off
REM Activate virtual environment
call venv\Scripts\activate

REM Install dependencies if not present
if not exist requirements.txt (
    echo requirements.txt not found. Please run install.bat first.
    pause
    exit /b
)

pip install -r requirements.txt --quiet

REM Run with Gunicorn for production
setlocal enabledelayedexpansion
if defined TRANSCRIPTION_PORT (
    set "PORT=!TRANSCRIPTION_PORT!"
) else (
    set "PORT=5123"
)
gunicorn -c gunicorn.conf.py app:app
pause