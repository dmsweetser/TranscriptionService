#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# Install dependencies if not present
if [ ! -f requirements.txt ]; then
    echo "requirements.txt not found. Please run install.sh first."
    exit 1
fi

pip install -r requirements.txt --quiet

# Run with Gunicorn for production
gunicorn -c gunicorn.conf.py app:app