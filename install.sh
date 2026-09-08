#!/bin/bash

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Generate secure admin password hash if not present
if ! grep -q "ADMIN_PASSWORD_HASH" .env; then
    echo "Generating secure admin password hash..."
    ADMIN_PASS=$(grep -oP '^ADMIN_PASSWORD=\K.*' .env)
    if [ -n "$ADMIN_PASS" ]; then
        HASH=$(python3 -c "import bcrypt; print(bcrypt.hashpw(b'$ADMIN_PASS', bcrypt.gensalt()).decode())")
        sed -i "s/^ADMIN_PASSWORD=.*/ADMIN_PASSWORD_HASH=$HASH/" .env
        echo "Admin password hash generated. Please keep your .env file secure."
    else
        echo "Warning: ADMIN_PASSWORD not found in .env. Please set it and run install.sh again."
    fi
fi

echo "Installation complete!"
echo "To run the application, execute: ./run.sh"