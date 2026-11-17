import json
import logging
import re
from datetime import UTC, datetime
from typing import Any

_CONTEXT_FIELDS = frozenset(
    {
        "agent",
        "case_id",
        "duration_ms",
        "error_type",
        "final_status",
        "message_length",
        "proposal",
        "queue_new",
        "reason_code",
        "return_id",
        "status",
    }
)
_SECRET_PATTERN = re.compile(
    r"(postgres(?:ql)?://[^\s\"']*:[^\s\"'@]+@|Bearer\s+\S+|"
    r"(?:sk-|gsk_)[A-Za-z0-9_-]{12,})",
    re.IGNORECASE,
)
_configured = False


class _JsonFormatter(logging.Formatter):
    @staticmethod
    def _redact(value: str) -> str:
        return _SECRET_PATTERN.sub("[REDACTED]", value)

    def format(self, record: logging.LogRecord) -> str:
        event: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname.lower(),
            "logger": record.name,
            "message": self._redact(record.getMessage()),
        }
        for field in _CONTEXT_FIELDS:
            if field in record.__dict__:
                event[field] = record.__dict__[field]
        if record.exc_info:
            event["exception"] = self._redact(
                self.formatException(record.exc_info)
            )
        return json.dumps(event, default=str)


def get_logger(name: str) -> logging.Logger:
    """Return a standard logger for a worker pipeline module."""
    return logging.getLogger(name)


def configure_logging(level: int = logging.INFO) -> None:
    """Configure consistent JSON logging once for the worker process."""
    global _configured
    if _configured:
        return

    logging.basicConfig(level=level, format="%(message)s")
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    for handler in root_logger.handlers:
        handler.setFormatter(_JsonFormatter())
    _configured = True
