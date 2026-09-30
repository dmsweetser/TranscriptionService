#!/bin/bash
set -e

# ─── TranscriptionService – Linux/macOS Run Script ───
# Usage: ./run.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment
source venv/bin/activate

# Install dependencies if not present
if [ ! -f requirements.txt ]; then
    echo "requirements.txt not found. Please run install.sh first."
    exit 1
fi

pip install -r requirements.txt --quiet 2>/dev/null || true

# Run with Gunicorn for production
exec gunicorn -c gunicorn.conf.py app:app
