# TranscriptionService - Windows 11 Production Deployment Guide

## Prerequisites
- Windows 11 (64-bit)
- Python 3.8+ (Download from python.org, ensure "Add Python to PATH" is checked)
- Administrator access (for firewall/service configuration)
- Stable internet connection for initial dependency installation
- Audio input device (microphone or loopback capture software like VB-Cable if needed)

## Step 1: Environment Setup
1. Open PowerShell as Administrator.
2. Navigate to your project directory:
   ```powershell
   cd C:\path\to\TranscriptionService
   ```
3. Create a virtual environment:
   ```powershell
   python -m venv venv
   ```
4. Activate the virtual environment:
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
   *Note: If you get a script execution policy error, run:*
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```
5. Upgrade pip and install dependencies:
   ```powershell
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

## Step 2: Configuration
1. Copy the example environment file:
   ```powershell
   copy .env.example .env
   ```
2. Edit `.env` with your production values:
   ```env
   ASSEMBLY_AI_API_KEY=your_real_assembly_ai_key_here
   ADMIN_PASSWORD=your_strong_password_here
   TRANSCRIPTION_PORT=5123
   TRANSLATION_PORT=5001
   DEFAULT_AUDIO_DEVICE=Your Audio Device Name
   BIAS_WORDS=transcription,translation,production
   SAVE_LOCATION=C:\transcriptions
   SECRET_KEY=generate_a_secure_random_string_here
   ALLOWED_ORIGINS=http://localhost:5123,https://yourdomain.com
   ```
3. Generate the secure password hash:
   ```powershell
   .\install.bat
   ```
   *This will replace `ADMIN_PASSWORD` with `ADMIN_PASSWORD_HASH` in `.env`.*

## Step 3: Directory Permissions
1. Create the save directory and set permissions:
   ```powershell
   mkdir C:\transcriptions
   icacls C:\transcriptions /grant Users:(OI)(CI)M
   ```

## Step 4: Firewall Configuration
1. Open Windows Defender Firewall with Advanced Security.
2. Create an Inbound Rule for TCP ports `5123` and `5001`.
3. Allow the connection for Domain, Private, and Public profiles.
4. Name the rule `TranscriptionService-Ports`.

## Step 5: Production Service Deployment
Option A: Manual Start (Development/Testing)
```powershell
.\run.bat
```

Option B: Windows Service (Production Recommended)
1. Install NSSM (Non-Sucking Service Manager):
   ```powershell
   choco install nssm
   ```
2. Register the service:
   ```powershell
   nssm install TranscriptionService
   ```
3. In the NSSM GUI:
   - **Path**: `C:\path\to\TranscriptionService\venv\Scripts\gunicorn.exe`
   - **Arguments**: `-c gunicorn.conf.py app:app`
   - **Startup directory**: `C:\path\to\TranscriptionService`
   - **Standard output**: `C:\path\to\TranscriptionService\logs\stdout.log`
   - **Standard error**: `C:\path\to\TranscriptionService\logs\stderr.log`
   - **App parameters**: `--workers 4 --timeout 120 --bind 0.0.0.0:5123`
4. Start the service:
   ```powershell
   nssm start TranscriptionService
   ```

## Step 6: Verification
1. Check service health:
   ```powershell
   curl http://localhost:5123/health
   ```
2. Access admin panel:
   ```
   http://localhost:5123/admin
   ```
3. Verify transcription stream:
   ```powershell
   curl http://localhost:5123/api/transcription/stream
   ```

## Troubleshooting
- **Audio device not found**: Run `python -c "import sounddevice as sd; print(sd.query_devices())"` to verify device names. Update `DEFAULT_AUDIO_DEVICE` in `.env`.
- **Permission denied on logs**: Ensure the service account has write access to the project directory.
- **CORS errors**: Update `ALLOWED_ORIGINS` in `.env` to include your frontend domain.
- **High CPU usage**: Reduce `GUNICORN_WORKERS` in `.env` or adjust `BIAS_WORDS` to reduce processing load.

## Maintenance
- **Logs**: Located in `app.log` and `logs/` directory.
- **Transcriptions**: Stored in `C:\transcriptions\` as `.txt` files.
- **Updates**: Pull new code, activate venv, run `pip install -r requirements.txt`, and restart the service.
- **Backups**: Regularly backup `.env`, `app.log`, and `C:\transcriptions\` directory.