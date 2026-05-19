"""
Verify DATABASE_URL connectivity and tables (same as setup_database.py).
"""
from __future__ import annotations

import asyncio
import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger("test_db")


async def test_connection() -> bool:
    try:
        from database import check_db_connection, init_db, AsyncSessionLocal, Message
        from sqlalchemy import select
    except ValueError as exc:
        logger.error("%s", exc)
        logger.error("Set DATABASE_URL in BACKEND/.env (no quotes needed)")
        return False

    if not await check_db_connection():
        logger.error("Connection failed — check DATABASE_URL and that Postgres is running")
        return False
    logger.info("Connected")

    await init_db()
    logger.info("Tables OK")

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Message).limit(1))
        if result.scalars().first():
            logger.info("Messages table has data")
        else:
            logger.info("Messages table empty (OK for new DB)")

    logger.info("All database checks passed")
    return True


if __name__ == "__main__":
    ok = asyncio.run(test_connection())
    sys.exit(0 if ok else 1)
