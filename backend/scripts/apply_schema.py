from __future__ import annotations

import asyncio
from pathlib import Path

import asyncpg

from app.config import settings


def _to_asyncpg_dsn(database_url: str) -> str:
    if database_url.startswith("postgresql+asyncpg://"):
        return database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql://", 1)
    return database_url


async def main() -> None:
    schema_path = Path(__file__).resolve().parents[1] / "db" / "schema.sql"
    schema_sql = schema_path.read_text(encoding="utf-8")
    conn = await asyncpg.connect(_to_asyncpg_dsn(settings.database_url))
    try:
        await conn.execute(schema_sql)
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
