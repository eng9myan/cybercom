"""
Structured JSON logging config for platform services.

Prefers ``structlog`` when installed; otherwise falls back to a stdlib JSON
formatter. Every emitted record carries::

    { "service": "...", "env": "...", "tenant_id": "...",
      "request_id": "...", "timestamp": "...", "level": "...", "message": "..." }

Import :func:`build_logging_config` and assign the result to
``settings.LOGGING``.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict

# ---------------------------------------------------------------------------
# thread-local context (populated by observability.middleware.RequestIdMiddleware)
# ---------------------------------------------------------------------------
try:
    import contextvars  # py3.7+

    _request_id_var: "contextvars.ContextVar[str]" = contextvars.ContextVar(
        "request_id", default=""
    )
    _tenant_id_var: "contextvars.ContextVar[str]" = contextvars.ContextVar(
        "tenant_id", default=""
    )
except ImportError:  # pragma: no cover
    _request_id_var = None  # type: ignore[assignment]
    _tenant_id_var = None  # type: ignore[assignment]


def bind_request_context(request_id: str = "", tenant_id: str = "") -> None:
    """Store request-scoped log context — middleware calls this per request."""
    if _request_id_var is not None:
        _request_id_var.set(request_id or "")
    if _tenant_id_var is not None:
        _tenant_id_var.set(tenant_id or "")


def clear_request_context() -> None:
    if _request_id_var is not None:
        _request_id_var.set("")
    if _tenant_id_var is not None:
        _tenant_id_var.set("")


def _current_request_id() -> str:
    return _request_id_var.get() if _request_id_var is not None else ""


def _current_tenant_id() -> str:
    return _tenant_id_var.get() if _tenant_id_var is not None else ""


# ---------------------------------------------------------------------------
# stdlib JSON formatter fallback
# ---------------------------------------------------------------------------
_RESERVED = {
    "args", "asctime", "created", "exc_info", "exc_text", "filename", "funcName",
    "levelname", "levelno", "lineno", "message", "module", "msecs", "msg", "name",
    "pathname", "process", "processName", "relativeCreated", "stack_info",
    "thread", "threadName",
}


class JsonFormatter(logging.Formatter):
    """Emit a single-line JSON object per log record."""

    def __init__(self, service: str, env: str) -> None:
        super().__init__()
        self.service = service
        self.env = env

    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": self.service,
            "env": self.env,
            "request_id": getattr(record, "request_id", None) or _current_request_id(),
            "tenant_id": getattr(record, "tenant_id", None) or _current_tenant_id(),
        }
        # Merge structured ``extra`` fields (skip reserved).
        for key, value in record.__dict__.items():
            if key in _RESERVED or key in payload or key.startswith("_"):
                continue
            try:
                json.dumps(value)
                payload[key] = value
            except (TypeError, ValueError):
                payload[key] = repr(value)

        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def _structlog_available() -> bool:
    try:
        import structlog  # noqa: F401
        return True
    except ImportError:
        return False


def build_logging_config(
    *,
    service: str = "cymed-platform",
    env: str = "development",
    level: str = "INFO",
) -> Dict[str, Any]:
    """
    Return a ``LOGGING`` dict suitable for ``settings.LOGGING``.

    If ``structlog`` is importable, its processor chain is used at import time
    inside the calling module. This function only returns the stdlib
    ``logging.config.dictConfig`` payload — the formatter is stdlib either way,
    which keeps compatibility with third-party libraries that use
    ``logging.getLogger`` directly.
    """
    formatter_path = f"{JsonFormatter.__module__}.{JsonFormatter.__name__}"

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": formatter_path,
                "service": service,
                "env": env,
            },
            "simple": {
                "format": "[%(asctime)s] %(levelname)s %(name)s: %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json",
                "level": level,
            },
        },
        "root": {"handlers": ["console"], "level": level},
        "loggers": {
            "django": {"handlers": ["console"], "level": "WARNING", "propagate": False},
            "django.request": {
                "handlers": ["console"],
                "level": "ERROR",
                "propagate": False,
            },
            "cybercom": {"handlers": ["console"], "level": level, "propagate": False},
            "cybercom.audit": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            "cybercom.observability": {
                "handlers": ["console"],
                "level": level,
                "propagate": False,
            },
            "cybercom.security": {
                "handlers": ["console"],
                "level": level,
                "propagate": False,
            },
        },
    }


def default_logging_config() -> Dict[str, Any]:
    """Convenience wrapper reading service/env from environment."""
    return build_logging_config(
        service=os.environ.get("OTEL_SERVICE_NAME", "cymed-platform"),
        env=os.environ.get("ENVIRONMENT", "development"),
        level=os.environ.get("LOG_LEVEL", "INFO"),
    )


# Convenience alias — matches the settings-import name callers use.
build_logging = build_logging_config


__all__ = [
    "JsonFormatter",
    "bind_request_context",
    "clear_request_context",
    "build_logging",
    "build_logging_config",
    "default_logging_config",
]

_ = _structlog_available  # keep helper referenced for future use
