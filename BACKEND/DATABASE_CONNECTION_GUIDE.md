# PostgreSQL Database Connection Guide

## Quick Setup Steps

### Step 1: Find Your PostgreSQL Password

If you don't remember your PostgreSQL password, you have a few options:

**Option A: Check if you set it during installation**
- During PostgreSQL installation, you were asked to set a password for the `postgres` user
- Check any notes or documentation from when you installed PostgreSQL

**Option B: Reset the password (if you have admin access)**
1. Open Command Prompt as Administrator
2. Navigate to PostgreSQL bin directory (usually `C:\Program Files\PostgreSQL\<version>\bin`)
3. Run: `psql -U postgres`
4. If that doesn't work, you may need to reset via pgAdmin or the Windows service

**Option C: Use pgAdmin (if installed)**
- Open pgAdmin
- Connect to your PostgreSQL server
- The password you use there is the one you need

### Step 2: Configure Database Credentials

Run the interactive configuration script:

```bash
cd BACKEND
python configure_db_credentials.py
```

This will prompt you for:
- PostgreSQL Username (usually `postgres`)
- PostgreSQL Password (the one you set during installation)
- Host (usually `localhost`)
- Port (usually `5432`)
- Database Name (will be created automatically: `voice_assistant_db`)

### Step 3: Test Connection and Create Database

After configuring credentials, run:

```bash
python setup_database.py
```

This script will:
- Test the PostgreSQL server connection
- Create the `voice_assistant_db` database if it doesn't exist
- Verify the connection works

### Step 4: Start Your Application

Once the database is set up, start your FastAPI server:

```bash
python main.py
```

The application will automatically:
- Connect to PostgreSQL
- Create the `messages` table on startup
- Start storing all chat messages in the database

## Manual Configuration

If you prefer to edit the `.env` file manually:

1. Open `BACKEND/.env` in a text editor
2. Add or update the `DATABASE_URL` line:
   ```
   DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/voice_assistant_db
   ```
3. Replace `YOUR_PASSWORD` with your actual PostgreSQL password

## Troubleshooting

### "password authentication failed"
- **Solution**: Your PostgreSQL password in `.env` is incorrect
- Run `python configure_db_credentials.py` to update it

### "database does not exist"
- **Solution**: Run `python setup_database.py` to create the database automatically

### "connection refused" or "could not connect"
- **Solution**: Make sure PostgreSQL service is running
- Check Windows Services: `services.msc` → Look for "postgresql" service
- Start the service if it's stopped

### "ModuleNotFoundError: No module named 'asyncpg'"
- **Solution**: Install dependencies:
  ```bash
  pip install asyncpg sqlalchemy psycopg2-binary
  ```

## Verifying the Connection

After setup, you can verify everything works by:

1. Starting the server: `python main.py`
2. Look for this message in the console: `✅ Database initialized successfully`
3. Make a test API call to `/ask-and-speak?question=test`
4. Check the database - messages should be stored automatically

## Database Schema

The `messages` table structure:
- `id`: Auto-incrementing primary key
- `text`: Message content (Text)
- `sender`: Either "user" or "bot" (String, 50 chars)
- `created_at`: Timestamp (DateTime with timezone)

## Next Steps

Once connected:
- All user questions and bot responses are automatically saved
- Use the `/messages` endpoint to retrieve stored messages
- The database persists all conversation history

