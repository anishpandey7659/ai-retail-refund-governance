from psycopg.rows import dict_row
from typing import LiteralString
from worker.pipeline.config import get_settings
from psycopg_pool import AsyncConnectionPool

_pool = AsyncConnectionPool(
    conninfo=get_settings().database_url,
    min_size=1,
    max_size=4,
    open=False, # Don't open connections until first use
)

async def _rows(sql: LiteralString, params: dict):
    async with _pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(sql, params)
            return await cur.fetchall()


async def startup(ctx: dict):
    print("Starting ARQ worker...")
    await _pool.open()
    ctx["db_pool"] = _pool
    print("Database connected!")


async def shutdown(ctx: dict):
    print("Shutting down ARQ worker...")
    db_pool = ctx.get("db_pool")
    if db_pool:
        await db_pool.close()
    print("Database connection closed!")
