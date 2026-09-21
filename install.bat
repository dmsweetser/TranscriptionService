@echo off
REM Create virtual environment
python -m venv venv

REM Activate virtual environment
call venv\Scripts\activate

REM Upgrade pip
pip install --upgrade pip

REM Install dependencies
pip install -r requirements.txt

REM Generate secure admin password hash if not present
python setup_admin.py

echo Installation complete!
echo To run the application, execute: run.bat
pause