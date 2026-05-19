# PostgreSQL Database Setup

This guide will help you set up PostgreSQL for storing messages in the Voice Assistant application.

## Prerequisites

1. **PostgreSQL installed** on your system
   - Download from: https://www.postgresql.org/download/
   - Or use Docker: `docker run --name postgres -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres`

## Setup Steps

### 1. Create the Database

Connect to PostgreSQL and create the database:

```sql
CREATE DATABASE voice_assistant_db;
```

### 2. Configure Environment Variables

Create a `.env` file in the `BACKEND` directory (copy from `.env.example`):

```bash
# Groq API Key
GROQ_API_KEY=your_groq_api_key_here

# PostgreSQL Database Connection
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/voice_assistant_db
```

**Update the DATABASE_URL with your actual credentials:**
- Replace `postgres` (username) with your PostgreSQL username
- Replace `postgres` (password) with your PostgreSQL password
- Replace `localhost` with your database host if different
- Replace `5432` with your PostgreSQL port if different
- Replace `voice_assistant_db` with your database name if different

### 3. Install Dependencies

The backend will automatically install required packages when you run `main.py`, but you can also install manually:

```bash
pip install sqlalchemy asyncpg psycopg2-binary
```

### 4. Run the Application

When you start the FastAPI server, it will automatically:
- Connect to PostgreSQL
- Create the `messages` table if it doesn't exist
- Start storing messages in the database

```bash
cd BACKEND
python main.py
# or
uvicorn main:app --reload
```

## Database Schema

The `messages` table has the following structure:

- `id` (Integer, Primary Key): Unique identifier for each message
- `text` (Text): The message content
- `sender` (String, 50 chars): Either "user" or "bot"
- `created_at` (DateTime): Timestamp when the message was created

## Troubleshooting

### Connection Errors

If you see connection errors, check:
1. PostgreSQL is running: `pg_isready` or check the service status
2. Database credentials in `.env` are correct
3. Database exists: `psql -U postgres -l` to list databases
4. Firewall allows connections on port 5432

### Common Issues

**"ModuleNotFoundError: No module named 'asyncpg'"**
- Install dependencies: `pip install asyncpg sqlalchemy`

**"FATAL: password authentication failed"**
- Verify your PostgreSQL username and password in `.env`

**"database does not exist"**
- Create the database: `CREATE DATABASE voice_assistant_db;`

**"relation 'messages' does not exist"**
- The table should be created automatically on startup. Check the startup logs for errors.

