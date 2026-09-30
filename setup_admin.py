import bcrypt
import os
import sys


def setup_admin_hash():
    """Read ADMIN_PASSWORD from .env, hash it with bcrypt, write ADMIN_PASSWORD_HASH."""
    env_path = ".env"
    if not os.path.exists(env_path):
        print(f"Error: {env_path} not found.")
        sys.exit(1)

    with open(env_path, "r") as f:
        content = f.read()

    # Check if hash already exists
    if "ADMIN_PASSWORD_HASH=" in content:
        print("Admin password hash already exists. Skipping.")
        return

    # Check for plain-text password
    import re
    match = re.search(r"^ADMIN_PASSWORD=(.*)$", content, re.MULTILINE)
    if not match:
        print("Error: ADMIN_PASSWORD not found in .env.")
        print("Please add ADMIN_PASSWORD=your_password to .env first.")
        sys.exit(1)

    password = match.group(1).strip()
    if not password:
        print("Error: ADMIN_PASSWORD is empty in .env.")
        sys.exit(1)

    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    # Replace the file: remove ADMIN_PASSWORD line, add ADMIN_PASSWORD_HASH
    new_lines = []
    for line in content.splitlines():
        if line.startswith("ADMIN_PASSWORD=") and not line.startswith("ADMIN_PASSWORD_HASH"):
            continue  # skip the plain-text password
        new_lines.append(line)
    new_lines.append(f"ADMIN_PASSWORD_HASH={hashed}")

    with open(env_path, "w") as f:
        f.write("\n".join(new_lines))

    print("Admin password hash generated. Please keep your .env file secure.")
    print(f"Hash: {hashed}")


if __name__ == "__main__":
    setup_admin_hash()
