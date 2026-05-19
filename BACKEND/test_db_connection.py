"""
Quick test script to verify database connection and table creation.
Run this after configuring your PostgreSQL credentials.
"""
import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv
import os

# Add parent directory to path
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH)

async def test_connection():
    """Test database connection and table creation."""
    try:
        from database import engine, init_db, Message, AsyncSessionLocal
        from sqlalchemy import select
        
        print("Testing database connection...")
        
        # Test 1: Connect to database
        async with engine.begin() as conn:
            print("SUCCESS: Connected to database")
        
        # Test 2: Initialize tables
        print("Creating tables...")
        await init_db()
        print("SUCCESS: Tables created/verified")
        
        # Test 3: Insert a test message
        print("Testing message insertion...")
        async with AsyncSessionLocal() as session:
            test_message = Message(
                text="Test message from setup script",
                sender="bot"
            )
            session.add(test_message)
            await session.commit()
            await session.refresh(test_message)
            print(f"SUCCESS: Test message inserted with ID: {test_message.id}")
        
        # Test 4: Query messages
        print("Testing message retrieval...")
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Message).limit(1))
            messages = result.scalars().all()
            if messages:
                print(f"SUCCESS: Retrieved {len(messages)} message(s)")
            else:
                print("WARNING: No messages found (this is OK if database is new)")
        
        print("\n" + "="*60)
        print("SUCCESS: All database tests passed!")
        print("="*60)
        print("\nYour backend is ready to store data in PostgreSQL.")
        print("Start your server with: python main.py")
        return True
        
    except Exception as e:
        print("\n" + "="*60)
        print("ERROR: Database test failed")
        print("="*60)
        print(f"Error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure PostgreSQL is running")
        print("2. Check your DATABASE_URL in .env file")
        print("3. Run 'python configure_db_credentials.py' to update credentials")
        print("4. Run 'python setup_database.py' to create the database")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_connection())
    sys.exit(0 if success else 1)

