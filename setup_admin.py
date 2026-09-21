import bcrypt
import os
import sys

def setup_admin_hash():
    env_path = '.env'
    if not os.path.exists(env_path):
        print(f"Error: {env_path} not found.")
        sys.exit(1)
    
    with open(env_path, 'r') as f:
        content = f.read()
    
    if 'ADMIN_PASSWORD_HASH' in content:
        print("Admin password hash already exists. Skipping.")
        return
    
    if 'ADMIN_PASSWORD=' not in content:
        print("Error: ADMIN_PASSWORD not found in .env.")
        sys.exit(1)
        
    lines = content.splitlines()
    new_lines = []
    for line in lines:
        if line.startswith('ADMIN_PASSWORD='):
            password = line.split('=', 1)[1]
            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            new_lines.append(f'ADMIN_PASSWORD_HASH={hashed}')
        else:
            new_lines.append(line)
            
    with open(env_path, 'w') as f:
        f.write('\n'.join(new_lines))
    print("Admin password hash generated. Please keep your .env file secure.")

if __name__ == '__main__':
    setup_admin_hash()