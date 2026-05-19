"""
Interactive script to configure PostgreSQL database credentials.
"""
import os
from pathlib import Path
from dotenv import set_key, dotenv_values

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

def main():
    print("=" * 60)
    print("PostgreSQL Database Credentials Configuration")
    print("=" * 60)
    print()
    print("Please provide your PostgreSQL connection details.")
    print("(Press Enter to use default values shown in brackets)")
    print()
    
    # Get current values if they exist
    env_vars = dotenv_values(ENV_PATH)
    current_url = env_vars.get("DATABASE_URL", "")
    
    # Parse current URL if it exists
    default_user = "postgres"
    default_password = "postgres"
    default_host = "localhost"
    default_port = "5432"
    default_database = "voice_assistant_db"
    
    if current_url and "postgresql+asyncpg://" in current_url:
        try:
            url_part = current_url.replace("postgresql+asyncpg://", "")
            user_pass, host_port_db = url_part.split("@")
            user, password = user_pass.split(":")
            host_port, database = host_port_db.split("/")
            if ":" in host_port:
                host, port = host_port.split(":")
            else:
                host = host_port
                port = "5432"
            
            default_user = user
            default_password = password
            default_host = host
            default_port = port
            default_database = database
        except:
            pass
    
    # Get user input
    print(f"PostgreSQL Username [{default_user}]: ", end="")
    user = input().strip() or default_user
    
    print(f"PostgreSQL Password [{default_password}]: ", end="")
    password = input().strip() or default_password
    
    print(f"PostgreSQL Host [{default_host}]: ", end="")
    host = input().strip() or default_host
    
    print(f"PostgreSQL Port [{default_port}]: ", end="")
    port = input().strip() or default_port
    
    print(f"Database Name [{default_database}]: ", end="")
    database = input().strip() or default_database
    
    # Construct DATABASE_URL
    database_url = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"
    
    # Update .env file
    set_key(ENV_PATH, "DATABASE_URL", database_url)
    
    print()
    print("=" * 60)
    print("SUCCESS: DATABASE_URL has been updated in .env file")
    print("=" * 60)
    print(f"Connection string: postgresql+asyncpg://{user}:***@{host}:{port}/{database}")
    print()
    print("Next step: Run 'python setup_database.py' to test the connection and create the database.")
    print()

if __name__ == "__main__":
    main()

