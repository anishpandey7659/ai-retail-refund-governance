from worker.pipeline.config import redis_settings
from worker.pipeline.db import startup as db_startup, shutdown as db_shutdown
from worker.pipeline.jobs import review_return


class WorkerSettings:
    # Functions registered as background jobs
    functions = [
        review_return,
    ]

    # Redis connection
    redis_settings = redis_settings()

    on_startup = db_startup
    on_shutdown = db_shutdown

    # Worker configuration
    max_jobs = 10
    job_timeout = 300
    max_tries = 3

    # Worker name
    queue_name = "arq:queue"


# uv run arq worker.pipeline.worker.WorkerSettings