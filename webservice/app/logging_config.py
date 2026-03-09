"""
Structured logging to stdout/stderr. PRD: logging to stdout and stderr is important.
Errors go to stderr; info/debug to stdout. No file logging by default.
"""
import logging
import sys
from typing import Any

# Use standard logging; ensure no uncaught handler failures
LOG_FORMAT = "%(asctime)s.%(msecs)03d %(levelname)s [%(name)s] %(message)s"
DATE_FMT = "%Y-%m-%dT%H:%M:%S"


def _safe_extra(extra: dict[str, Any] | None) -> dict[str, Any]:
    if not extra:
        return {}
    # Avoid LogRecord reserved names: message, msg, args, etc.
    reserved = {"message", "msg", "args", "levelname", "levelno", "pathname", "filename", "module", "lineno", "funcName", "created", "thread", "threadName", "process", "processName", "stack_info", "exc_info", "exc_text", "taskName"}
    return {k: v for k, v in extra.items() if k not in reserved}


class StructuredFormatter(logging.Formatter):
    """Format with optional extra fields for structured logs."""

    def format(self, record: logging.LogRecord) -> str:
        base = super().format(record)
        extra = getattr(record, "extra", None) or {}
        if not extra:
            return base
        parts = [f"{k}={v!r}" for k, v in _safe_extra(extra).items()]
        if parts:
            return f"{base} | {', '.join(parts)}"
        return base


def configure_logging(log_level: str = "INFO") -> None:
    """Configure root logger: stdout for INFO and below, stderr for WARNING and above."""
    root = logging.getLogger()
    root.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Avoid duplicate handlers on reload
    if root.handlers:
        return

    formatter = StructuredFormatter(LOG_FORMAT, datefmt=DATE_FMT)

    out = logging.StreamHandler(sys.stdout)
    out.setLevel(logging.DEBUG)
    out.addFilter(lambda r: r.levelno < logging.WARNING)
    out.setFormatter(formatter)
    root.addHandler(out)

    err = logging.StreamHandler(sys.stderr)
    err.setLevel(logging.WARNING)
    err.setFormatter(formatter)
    root.addHandler(err)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
