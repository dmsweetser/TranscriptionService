# TranscriptionService

A real-time transcription and translation service using Assembly AI.

## Features

- Real-time transcription from computer audio stream
- Local translation with separate streams
- Admin GUI for service control and configuration
- User-facing web interfaces for transcription/translation
- QR code access for users
- Support for multiple languages (English, French, Spanish, Arabic)
- Secure admin authentication

## Setup

### Prerequisites

- Python 3.8+
- pip
- Virtual environment support

### Installation

Run the installation script for your OS:

```bash
# On Windows
install.bat

# On Linux/macOS
./install.sh
```

### Running the Service

```bash
# On Windows
run.bat

# On Linux/macOS
./run.sh
```

## Configuration

Sensitive keys are stored in `.env` file. Example:

```
ASSEMBLY_AI_API_KEY=your_assembly_ai_key_here
ADMIN_PASSWORD=your_admin_password_here
TRANSCRIPTION_PORT=5000
TRANSLATION_PORT=5001
```

## Admin Interface

Access the admin panel by navigating to `/admin` and entering the admin password from `.env`.

## User Interface

Users can access transcription and translation streams via QR codes or direct URLs.

## Development

To run in development mode with mocks:

```bash
python app.py --mock
```

## Testing

Mock endpoints are available for testing:
- `/mock/transcription`
- `/mock/translation`
- `/mock/audio_devices`
- `/mock/translation_languages`