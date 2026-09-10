"""Structured JSON logging with a per-run correlation ID (run_id).

Each log line is a JSON object on stderr. Secrets must never be logged.
"""

from __future__ import annotations

import json
import logging
import sys
import uuid
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

_RUN_ID: ContextVar[str] = ContextVar("run_id", default="no-run")


def set_run_id(run_id: str) -> str:
    _RUN_ID.set(run_id)
    return run_id


def new_run_id() -> str:
    return uuid.uuid4().hex[:8]


def _emit(level: str, message: str, **fields: Any) -> None:
    record: dict[str, Any] = {
        "timestamp": datetime.now(UTC).isoformat(),
        "run_id": _RUN_ID.get(),
        "level": level,
        "event": message,
    }
    record.update(fields)
    line = json.dumps(record, default=str)
    print(line, file=sys.stderr, flush=True)


class JsonLogger:
    """Minimal structured logger with keyword-only kv fields."""

    def info(self, message: str, **fields: Any) -> None:
        _emit("INFO", message, **fields)

    def warning(self, message: str, **fields: Any) -> None:
        _emit("WARNING", message, **fields)

    def error(self, message: str, **fields: Any) -> None:
        _emit("ERROR", message, **fields)

    def debug(self, message: str, **fields: Any) -> None:
        _emit("DEBUG", message, **fields)


_loggers: dict[str, JsonLogger] = {}


def get_logger(name: str) -> JsonLogger:
    if name not in _loggers:
        _loggers[name] = JsonLogger()
    return _loggers[name]


# Keep stdlib logger configured in case a dependency logs in our process style.
logging.basicConfig(level=logging.WARNING)