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
    HASH=$(python3 -c "import bcrypt; print(bcrypt.hashpw(b'$(grep ADMIN_PASSWORD .env | cut -d= -f2)', bcrypt.gensalt()).decode())")
    sed -i "s/^ADMIN_PASSWORD=.*/ADMIN_PASSWORD_HASH=$HASH/" .env
    echo "Admin password hash generated. Please keep your .env file secure."
fi

echo "Installation complete!"
echo "To run the application, execute: ./run.sh"