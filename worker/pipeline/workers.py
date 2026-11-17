from typing import ClassVar

from worker.pipeline.config import redis_settings
from worker.pipeline.db import shutdown as db_shutdown
from worker.pipeline.db import startup as db_startup
from worker.pipeline.jobs import review_return
from worker.pipeline.logger import configure_logging, get_logger
from worker.pipeline.tracing import flush_langfuse

logger = get_logger(__name__)


async def startup(ctx: dict) -> None:
    configure_logging()
    logger.info("Starting ARQ worker")
    await db_startup(ctx)


async def shutdown(ctx: dict) -> None:
    try:
        await db_shutdown(ctx)
    finally:
        flush_langfuse()
        logger.info("ARQ worker shutdown complete")


class WorkerSettings:
    # Functions registered as background jobs
    functions: ClassVar[list] = [
        review_return,
    ]

    # Redis connection
    redis_settings = redis_settings()

    on_startup = startup
    on_shutdown = shutdown

    # Worker configuration
    max_jobs = 10
    job_timeout = 300
    max_tries = 3

    # Worker name
    queue_name = "arq:queue"


# uv run arq worker.pipeline.worker.WorkerSettings
