"""
Quick script to update PostgreSQL password in .env file.
Usage: python update_password.py YOUR_PASSWORD
"""
import sys
from pathlib import Path
from dotenv import set_key, dotenv_values

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

def update_password(new_password: str):
    """Update the password in DATABASE_URL."""
    # Load current .env
    env_vars = dotenv_values(ENV_PATH)
    current_url = env_vars.get("DATABASE_URL", "")
    
    if not current_url:
        print("ERROR: DATABASE_URL not found in .env file")
        print("Creating default DATABASE_URL...")
        database_url = f"postgresql+asyncpg://postgres:{new_password}@localhost:5432/voice_assistant_db"
    else:
        # Parse and update the URL
        if "postgresql+asyncpg://" in current_url:
            url_part = current_url.replace("postgresql+asyncpg://", "")
            user_pass, host_port_db = url_part.split("@")
            user, _ = user_pass.split(":")
            host_port, database = host_port_db.split("/")
            
            # Reconstruct with new password
            database_url = f"postgresql+asyncpg://{user}:{new_password}@{host_port}/{database}"
        else:
            print("ERROR: Invalid DATABASE_URL format")
            return False
    
    # Update .env file
    set_key(ENV_PATH, "DATABASE_URL", database_url)
    
    print("SUCCESS: Password updated in .env file")
    print(f"Updated DATABASE_URL: postgresql+asyncpg://{user}:***@{host_port}/{database}")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python update_password.py YOUR_PASSWORD")
        print("\nExample: python update_password.py mypassword123")
        sys.exit(1)
    
    password = sys.argv[1]
    if update_password(password):
        print("\nNext step: Run 'python setup_database.py' to test the connection.")
    else:
        sys.exit(1)

