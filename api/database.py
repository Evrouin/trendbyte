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
    pool = AsyncConnectionPool(
        conninfo=settings.database_url,
        min_size=2,
        max_size=10,
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
