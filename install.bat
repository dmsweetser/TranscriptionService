@echo off
REM === TranscriptionService – Windows Install Script ===
REM Usage: install.bat

setlocal enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo === TranscriptionService Installation ===

REM 1. Create virtual environment
echo [1/5] Creating virtual environment...
python -m venv venv

REM 2. Activate virtual environment
echo [2/5] Activating virtual environment...
call venv\Scripts\activate.bat

REM 3. Upgrade pip and install dependencies
echo [3/5] Installing Python dependencies...
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

REM 4. Create .env if it doesn't exist
if not exist .env (
    echo [4/5] Creating .env from example...
    copy .env.example .env >nul
    echo Created .env. Please edit it with your settings before running.
) else (
    echo [4/5] .env already exists, skipping.
)

REM 5. Generate password hash if plain-text password exists
findstr /C:"^ADMIN_PASSWORD=" .env >nul 2>&1
if !errorlevel! equ 0 (
    findstr /C:"^ADMIN_PASSWORD_HASH=" .env >nul 2>&1
    if !errorlevel! neq 0 (
        echo Generating secure admin password hash...
        python setup_admin.py
    )
)

REM 6. Create transcriptions directory
if not exist transcriptions mkdir transcriptions

echo.
echo === Installation complete! ===
echo 1. Edit .env with your settings (especially ASSEMBLYAI_API_KEY and ADMIN_PASSWORD)
echo 2. Run: run.bat
echo.
pause
