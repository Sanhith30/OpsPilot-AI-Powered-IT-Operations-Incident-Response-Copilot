from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, ClassVar, Dict, List, Optional

from pydantic import BaseModel, Field

from app.ai.tools.base import BaseTool
from app.repositories.app_log_repository import AppLogRepository


class SearchLogsInput(BaseModel):
    """Input schema for the search_logs tool."""

    keyword: Optional[str] = Field(
        None,
        description="Free-text keyword to search in log messages (full-text search).",
    )
    service_name: Optional[str] = Field(
        None,
        description="Filter logs by service name (partial match).",
    )
    level: Optional[str] = Field(
        None,
        description="Filter by log level: DEBUG, INFO, WARNING, ERROR, CRITICAL.",
    )
    environment: Optional[str] = Field(
        "Production",
        description="Deployment environment to filter by.",
    )
    trace_id: Optional[str] = Field(
        None,
        description="Distributed trace ID to correlate logs across services.",
    )
    from_time: Optional[str] = Field(
        None,
        description="ISO-8601 start timestamp for the time window (e.g. '2024-01-15T10:00:00Z').",
    )
    to_time: Optional[str] = Field(
        None,
        description="ISO-8601 end timestamp for the time window.",
    )
    limit: int = Field(
        50,
        ge=1,
        le=200,
        description="Maximum number of log entries to return.",
    )


class SearchLogsTool(BaseTool):
    """
    Searches structured application logs stored in core.app_logs.

    Use this tool to diagnose service errors, find correlated log patterns,
    trace distributed requests, or investigate time-bound error spikes.
    """

    name: ClassVar[str] = "search_logs"
    description: ClassVar[str] = (
        "Search application logs for errors, warnings, or patterns. "
        "Accepts keyword, service name, log level, trace ID, and time range filters. "
        "Returns matching log entries with timestamps and metadata."
    )
    args_schema: ClassVar[type[BaseModel]] = SearchLogsInput

    def __init__(self, *, log_repository: AppLogRepository) -> None:
        self._repo = log_repository

    def execute(self, validated_input: SearchLogsInput) -> Dict[str, Any]:
        from_dt: Optional[datetime] = None
        to_dt: Optional[datetime] = None

        if validated_input.from_time:
            try:
                from_dt = datetime.fromisoformat(
                    validated_input.from_time.replace("Z", "+00:00")
                )
            except ValueError:
                pass

        if validated_input.to_time:
            try:
                to_dt = datetime.fromisoformat(
                    validated_input.to_time.replace("Z", "+00:00")
                )
            except ValueError:
                pass

        logs = self._repo.search(
            keyword=validated_input.keyword,
            service_name=validated_input.service_name,
            level=validated_input.level,
            environment=validated_input.environment,
            trace_id=validated_input.trace_id,
            from_time=from_dt,
            to_time=to_dt,
            limit=validated_input.limit,
        )

        entries: List[Dict[str, Any]] = []
        for log in logs:
            entries.append(
                {
                    "log_id": log.log_id,
                    "service_name": log.service_name,
                    "level": log.level,
                    "message": log.message,
                    "logger_name": log.logger_name,
                    "trace_id": log.trace_id,
                    "host": log.host,
                    "environment": log.environment,
                    "logged_at": log.logged_at.isoformat() if log.logged_at else None,
                    "extra": log.extra or {},
                }
            )

        level_counts: Dict[str, int] = {}
        for e in entries:
            lvl = e["level"]
            level_counts[lvl] = level_counts.get(lvl, 0) + 1

        return {
            "total_returned": len(entries),
            "level_breakdown": level_counts,
            "logs": entries,
        }
