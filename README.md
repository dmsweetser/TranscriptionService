# TranscriptionService

Real-time transcription and translation service with admin controls. Captures computer audio, transcribes it via Assembly AI, and broadcasts live results in multiple languages.

## Quick Start

### Prerequisites
- Python 3.11+
- An audio input device (microphone, loopback capture, etc.)
- Assembly AI API key ([get one here](https://assemblyai.com))

### Installation

```bash
# Linux/macOS
./install.sh

# Windows
install.bat
```

### Configuration

Edit `.env` with your settings:

```env
ASSEMBLY_AI_API_KEY=your_assembly_ai_key_here
ADMIN_PASSWORD=your_strong_password_here
TRANSCRIPTION_PORT=5123
TRANSLATION_PORT=5001
DEFAULT_AUDIO_DEVICE=Default Audio Device
BIAS_WORDS=transcription,translation
SAVE_LOCATION=./transcriptions
```

Then generate the secure password hash:
```bash
python setup_admin.py
```

### Running

```bash
# Linux/macOS
./run.sh

# Windows
run.bat
```

The service starts on port 5123 by default.

## Accessing the Service

| Interface | URL | Description |
|-----------|-----|-------------|
| User (transcription) | `http://localhost:5123/` | Live transcription display |
| Admin panel | `http://localhost:5123/admin` | Service control & configuration |
| Health check | `http://localhost:5123/health` | JSON status endpoint |

### Remote Access
To access from other devices on your network, find your machine's IP address and navigate to `http://<IP>:5123/`. Users can scan the QR code on the user interface page to open the stream on their mobile device.

## Features

- **Real-time transcription** from computer audio via Assembly AI
- **Live translation** into English, French, Spanish, Arabic, German, Italian, Japanese, Korean
- **Admin dashboard** with service start/stop, device selection, and configuration
- **Secure admin authentication** with bcrypt password hashing
- **Word biasing** to improve transcription accuracy for domain-specific terms
- **Automatic transcription saving** to text files when the stream stops
- **Responsive UI** — works on desktop and mobile browsers
- **Auto-scroll** — newest text appears at bottom; scroll up to review history
- **Session-based access** — each user gets a unique session ID

## Architecture

```
Audio Input → AudioStreamer → TranscriptionService → TranslationService
                                    ↓                        ↓
                              Assembly AI API         Google Translate
                                    ↓                        ↓
                              SSE Streams (port 5123)   SSE Streams
                                    ↓                        ↓
                              Web Browsers (users)
```

The service runs as a single-process Flask application behind Gunicorn (1 worker). Multi-worker mode is not supported because the audio streamer maintains global state.

## Configuration Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `ASSEMBLY_AI_API_KEY` | *(empty)* | Your Assembly AI API key |
| `ADMIN_PASSWORD` | *(empty)* | Plain-text password (migrated to hash) |
| `ADMIN_PASSWORD_HASH` | *(empty)* | bcrypt hash of admin password |
| `TRANSCRIPTION_PORT` | `5123` | Port for transcription/translation streams |
| `TRANSLATION_PORT` | `5001` | Reserved for future use |
| `DEFAULT_AUDIO_DEVICE` | `Default Audio Device` | Audio input device name |
| `BIAS_WORDS` | *(empty)* | Comma-separated words to boost transcription accuracy |
| `SAVE_LOCATION` | `./transcriptions` | Directory for saved transcription files |
| `SECRET_KEY` | *(generated)* | Flask session secret key |
| `ALLOWED_ORIGINS` | `http://localhost:5123,http://localhost:5001` | CORS allowed origins |
| `GUNICORN_WORKERS` | `1` | Must be 1 (single-process required) |

## Admin Panel

The admin panel (`/admin`) provides:

1. **Service Control** — Start/stop the transcription pipeline
2. **Audio Device Selection** — Choose from a list of detected audio input devices
3. **API Key Management** — Update your Assembly AI key without restarting
4. **Port Configuration** — Change the transcription port
5. **Word Biasing** — Add domain-specific vocabulary to improve accuracy
6. **Save Location** — Set where transcription text files are stored
7. **Connection Monitoring** — View active connections and service health

All admin actions require authentication.

## User Interface

The user interface (`/`) provides:

1. **Live transcription** — Newest text at the bottom, scroll up for history
2. **Language tabs** — Switch between English, French, Spanish, Arabic, etc.
3. **Auto-scroll** — Automatically follows new text; resume on scroll-down
4. **Connection status** — Visual indicator of stream connectivity
5. **QR code** — Scan to open the stream on a mobile device

Text is automatically saved to files when the service stops. Users cannot access saved text after the stream ends — only the admin can retrieve saved files.

## Development

Run with mock transcription (no API key needed):

```bash
python app.py --mock --port 5123
```

## Troubleshooting

- **Audio device not found**: Run `python -c "import sounddevice as sd; print(sd.query_devices())"` to see available devices. Update `DEFAULT_AUDIO_DEVICE` in `.env`.
- **Permission denied on logs**: Ensure the service account has write access to the project directory.
- **CORS errors**: Update `ALLOWED_ORIGINS` in `.env` to include your domain.
- **Translation fails**: Google Translate has rate limits. The service handles failures gracefully by returning the original text.
- **High CPU usage**: Reduce `BIAS_WORDS` or increase the gap between transcription requests.

## Maintenance

- **Logs**: `app.log` in the project directory
- **Transcriptions**: `./transcriptions/` as `.txt` files
- **Backups**: Regularly backup `.env`, `app.log`, and `./transcriptions/`
