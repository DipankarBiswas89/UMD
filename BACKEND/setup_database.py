"""
Production-safe database verification for Render / managed PostgreSQL.

Does NOT:
  - use localhost fallbacks
  - run CREATE DATABASE (database must already exist on Render)

Usage:
  python setup_database.py
"""
from __future__ import annotations

import asyncio
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("setup_database")


async def main() -> bool:
    logger.info("Verifying DATABASE_URL and PostgreSQL connection...")

    try:
        from database import DATABASE_URL, check_db_connection, init_db
    except ValueError as exc:
        logger.error("%s", exc)
        logger.error("Set DATABASE_URL in Render → Environment → Environment Variables")
        return False

    # Log safe summary (no password)
    try:
        from urllib.parse import urlparse

        parsed = urlparse(DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://"))
        logger.info("Host: %s | Port: %s | Database: %s", parsed.hostname, parsed.port, parsed.path.lstrip("/"))
    except Exception:
        logger.info("DATABASE_URL is set")

    if not await check_db_connection():
        logger.error("Connection failed. Check Render Postgres status and DATABASE_URL.")
        return False

    logger.info("Connection successful")

    try:
        await init_db()
        logger.info("Tables initialized (create_all)")
    except Exception as exc:
        logger.error("Table initialization failed: %s", exc)
        return False

    logger.info("Database setup complete — ready for deployment")
    return True


if __name__ == "__main__":
    ok = asyncio.run(main())
    sys.exit(0 if ok else 1)
