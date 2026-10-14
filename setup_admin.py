import bcrypt
import os
import sys
import getpass


def setup_admin_hash(password=None):
    """Hash admin password and write ADMIN_PASSWORD_HASH to .env."""
    env_path = ".env"
    if not os.path.exists(env_path):
        print(f"Error: {env_path} not found.")
        sys.exit(1)

    if not password:
        password = getpass.getpass("Enter admin password: ")
        if not password:
            print("Password cannot be empty.")
            sys.exit(1)

    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    with open(env_path, "r") as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        if line.startswith("ADMIN_PASSWORD=") and not line.startswith("ADMIN_PASSWORD_HASH="):
            continue  # skip plain text password line
        new_lines.append(line)

    new_lines.append(f"ADMIN_PASSWORD_HASH={hashed}\n")

    with open(env_path, "w") as f:
        f.writelines(new_lines)

    print("Admin password hash generated successfully.")
    print(f"Hash: {hashed}")


if __name__ == "__main__":
    password = sys.argv[1] if len(sys.argv) > 1 else None
    setup_admin_hash(password)
