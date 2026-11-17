from typing import LiteralString

from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from worker.pipeline.config import get_settings
from worker.pipeline.logger import get_logger

_pool = AsyncConnectionPool(
    conninfo=get_settings().database_url,
    min_size=1,
    max_size=4,
    open=False, # Don't open connections until first use
)
logger = get_logger(__name__)

async def _rows(sql: LiteralString, params: dict):
    async with _pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(sql, params)
            return await cur.fetchall()


async def startup(ctx: dict):
    logger.info("Starting worker database connection")
    try:
        await _pool.open()
    except Exception:
        logger.exception("Could not open worker database connection")
        raise
    ctx["db_pool"] = _pool
    logger.info("Worker database connection established")


async def shutdown(ctx: dict):
    logger.info("Closing worker database connection")
    db_pool = ctx.get("db_pool")
    if db_pool:
        try:
            await db_pool.close()
        except Exception:
            logger.exception("Could not close worker database connection")
            raise
    logger.info("Worker database connection closed")
