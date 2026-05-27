from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

from psycopg import AsyncConnection
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from api.settings import get_settings

pool: AsyncConnectionPool | None = None


async def init_pool() -> None:
    global pool
    settings = get_settings()
    conninfo = settings.database_url
    if "sslmode" not in conninfo and "localhost" not in conninfo and "127.0.0.1" not in conninfo:
        conninfo += "?sslmode=require" if "?" not in conninfo else "&sslmode=require"
    pool = AsyncConnectionPool(
        conninfo=conninfo,
        min_size=1,
        max_size=5,
        open=False,
        kwargs={"row_factory": dict_row},
    )
    await pool.open()


async def close_pool() -> None:
    global pool
    if pool:
        await pool.close()
        pool = None


async def get_db() -> AsyncGenerator[AsyncConnection[dict[str, Any]], None]:
    assert pool is not None
    async with pool.connection() as conn:
        yield conn  # type: ignore[misc]
