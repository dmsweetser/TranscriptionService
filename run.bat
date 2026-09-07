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
gunicorn --bind 0.0.0.0:5050 --workers 4 --timeout 120 app:app
pause