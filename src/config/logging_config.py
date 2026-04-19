"""Structured logging configuration with correlation ID support."""

import logging
import sys
import uuid
from typing import Optional


class CorrelationFilter(logging.Filter):
    """Injects a correlation_id field into every log record."""

    def __init__(self) -> None:
        super().__init__()
        self._correlation_id: str = "-"

    def set_id(self, correlation_id: str) -> None:
        """Set the active correlation ID for the current operation."""
        self._correlation_id = correlation_id

    def clear(self) -> None:
        """Clear the correlation ID after an operation completes."""
        self._correlation_id = "-"

    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = self._correlation_id
        return True


# Module-level singleton — shared across all loggers in the process.
_correlation_filter = CorrelationFilter()


def configure_logging(
    level: int = logging.INFO,
    json_format: bool = False,
) -> None:
    """Configure root logger with correlation ID support.

    Call once at application entry point (e.g. ingestion script, FastAPI startup).

    Args:
        level: Logging level (default INFO).
        json_format: If True, emit single-line JSON records suitable for
                     Azure Monitor / Application Insights structured ingest.
                     If False, emit a human-readable format for local dev.
    """
    root = logging.getLogger()
    root.setLevel(level)

    # Avoid duplicate handlers if called more than once.
    if root.handlers:
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(_correlation_filter)

    if json_format:
        fmt = (
            '{"time":"%(asctime)s","level":"%(levelname)s",'
            '"logger":"%(name)s","correlation_id":"%(correlation_id)s",'
            '"message":"%(message)s"}'
        )
    else:
        fmt = "%(asctime)s [%(levelname)s] [%(correlation_id)s] %(name)s — %(message)s"

    handler.setFormatter(logging.Formatter(fmt, datefmt="%Y-%m-%dT%H:%M:%S"))
    root.addHandler(handler)


def set_correlation_id(correlation_id: Optional[str] = None) -> str:
    """Set a correlation ID for the current operation and return it.

    Args:
        correlation_id: Explicit ID to use.  If None, a short UUID is generated.

    Returns:
        The correlation ID that was set.
    """
    cid = correlation_id or str(uuid.uuid4())[:8]
    _correlation_filter.set_id(cid)
    return cid


def clear_correlation_id() -> None:
    """Clear the correlation ID after an operation completes."""
    _correlation_filter.clear()
