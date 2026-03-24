"""Database connection setup helpers."""

from __future__ import annotations

from sqlalchemy import text

from app.db.session import async_engine


async def check_database_connection() -> None:
    """Ping the database to verify connectivity."""
    async with async_engine.connect() as connection:
        await connection.execute(text("SELECT 1"))
