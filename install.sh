#!/bin/bash
set -e

# ─── TranscriptionService – Linux/macOS Install Script ───
# Usage: ./install.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== TranscriptionService Installation ==="

# 1. Create virtual environment
echo "[1/4] Creating virtual environment..."
python3 -m venv venv

# 2. Activate virtual environment
echo "[2/4] Activating virtual environment..."
source venv/bin/activate

# 3. Upgrade pip and install dependencies
echo "[3/4] Installing Python dependencies..."
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

# 4. Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "[4/4] Creating .env from example..."
    cp .env.example .env
    echo "Created .env. Please edit it with your settings before running."
else
    echo "[4/4] .env already exists, skipping."
fi

# 5. Generate password hash if plain-text password exists
if grep -q "^ADMIN_PASSWORD=" .env 2>/dev/null && ! grep -q "^ADMIN_PASSWORD_HASH=" .env 2>/dev/null; then
    echo "Generating secure admin password hash..."
    python3 setup_admin.py
fi

# 6. Create transcriptions directory
mkdir -p transcriptions

echo ""
echo "=== Installation complete! ==="
echo "1. Edit .env with your settings (especially ASSEMBLY_AI_API_KEY and ADMIN_PASSWORD)"
echo "2. Run: ./run.sh"
echo ""
