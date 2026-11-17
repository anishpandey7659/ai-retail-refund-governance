from collections.abc import Iterator
from contextlib import contextmanager
from functools import lru_cache
from typing import Any

from langfuse import Langfuse

from worker.pipeline.config import get_settings
from worker.pipeline.logger import get_logger

logger = get_logger(__name__)

@lru_cache(maxsize=1)
def get_langfuse_client() -> Langfuse | None:
    """Return a configured Langfuse client, or None when tracing is disabled."""
    settings=get_settings()
    public_key = settings.langfuse_public_key
    secret_key = settings.langfuse_secret_key
    if not public_key and not secret_key:
        return None
    if not public_key or not secret_key:
        logger.error(
            "Langfuse tracing disabled: both LANGFUSE_PUBLIC_KEY and "
            "LANGFUSE_SECRET_KEY are required."
        )
        return None

    try:
        return Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            base_url=settings.langfuse_base_url or None,
        )
    except Exception:
        logger.exception("Could not initialize Langfuse; tracing is disabled.")
        return None


@contextmanager
def observation(
    *,
    name: str,
    metadata: dict[str, Any] | None = None,
) -> Iterator[Any | None]:
    """Create an optional Langfuse span."""
    client = get_langfuse_client()
    if client is None:
        yield None
        return

    try:
        manager = client.start_as_current_observation(
            as_type="span",
            name=name,
            metadata=metadata,
        )
        span = manager.__enter__()
    except Exception:
        logger.exception("Could not start Langfuse observation %s.", name)
        yield None
        return

    try:
        yield span
    except BaseException:
        try:
            manager.__exit__(None, None, None)
        except Exception:
            logger.exception("Could not close failed Langfuse observation %s.", name)
        raise
    else:
        try:
            manager.__exit__(None, None, None)
        except Exception:
            logger.exception("Could not close Langfuse observation %s.", name)


def update_observation(
    span: Any | None,
    *,
    status: str,
    details: dict[str, Any] | None = None,
    error_type: str | None = None,
    input_data: Any | None = None,
    output_data: Any | None = None,
) -> None:
    """Attach execution metadata and optional payloads to an observation."""
    if span is None:
        return

    metadata = {"status": status}
    if details:
        metadata.update(details)
    output = output_data if output_data is not None else {"status": status}
    try:
        update: dict[str, Any] = {
            "output": output,
            "metadata": metadata,
            "level": "ERROR" if error_type else "DEFAULT",
            "status_message": error_type,
        }
        if input_data is not None:
            update["input"] = input_data
        span.update(**update)
    except Exception:
        logger.exception("Could not update a Langfuse observation.")


def flush_langfuse() -> None:
    """Flush queued telemetry during worker shutdown."""
    client = get_langfuse_client()
    if client is None:
        return
    try:
        client.flush()
    except Exception:
        logger.exception("Could not flush queued Langfuse observations.")
