from __future__ import annotations

import json
import logging
from contextvars import ContextVar
from datetime import datetime, timezone

request_id_context: ContextVar[str | None] = ContextVar(
    "request_id",
    default=None,
)


def set_request_id(request_id: str) -> None:
    request_id_context.set(request_id)


def get_request_id() -> str | None:
    return request_id_context.get()


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": get_request_id(),
        }

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        for field in (
            "event",
            "service",
            "operation",
            "investigation_id",
            "incident_id",
            "tool_name",
            "status",
            "duration_ms",
        ):
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value

        return json.dumps(
            payload,
            ensure_ascii=False,
            default=str,
        )


def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)
