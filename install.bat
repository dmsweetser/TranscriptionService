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
python -c "
import bcrypt
import os
env_path = '.env'
with open(env_path, 'r') as f:
    content = f.read()
if 'ADMIN_PASSWORD_HASH' not in content:
    password = content.split('ADMIN_PASSWORD=')[1].split('\n')[0]
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    content = content.replace('ADMIN_PASSWORD='+password, 'ADMIN_PASSWORD_HASH='+hashed)
    with open(env_path, 'w') as f:
        f.write(content)
    print('Admin password hash generated. Please keep your .env file secure.')
"

echo Installation complete!
echo To run the application, execute: run.bat
pause