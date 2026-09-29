from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import and_, or_, text
from sqlalchemy.orm import Session

from app.models.app_log import AppLog


class AppLogRepository:
    """
    Data-access layer for core.app_logs.
    Supports full-text keyword search, level/service filtering, and time-range queries.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, log: AppLog) -> AppLog:
        self.db.add(log)
        return log

    def search(
        self,
        *,
        keyword: Optional[str] = None,
        service_id: Optional[int] = None,
        service_name: Optional[str] = None,
        level: Optional[str] = None,
        environment: Optional[str] = None,
        trace_id: Optional[str] = None,
        from_time: Optional[datetime] = None,
        to_time: Optional[datetime] = None,
        limit: int = 50,
    ) -> List[AppLog]:
        q = self.db.query(AppLog)

        if service_id is not None:
            q = q.filter(AppLog.service_id == service_id)

        if service_name:
            q = q.filter(AppLog.service_name.ilike(f"%{service_name}%"))

        if level:
            q = q.filter(AppLog.level == level.upper())

        if environment:
            q = q.filter(AppLog.environment == environment)

        if trace_id:
            q = q.filter(AppLog.trace_id == trace_id)

        if from_time:
            q = q.filter(AppLog.logged_at >= from_time)

        if to_time:
            q = q.filter(AppLog.logged_at <= to_time)

        if keyword:
            # Use Postgres full-text search on message column
            tsquery_expr = text("to_tsquery('english', :kw)").bindparams(
                kw=self._to_tsquery_safe(keyword)
            )
            q = q.filter(AppLog.message.op("@@")(tsquery_expr))

        return q.order_by(AppLog.logged_at.desc()).limit(limit).all()

    @staticmethod
    def _to_tsquery_safe(keyword: str) -> str:
        """Convert a free-form keyword into a safe tsquery string."""
        words = [w.strip() for w in keyword.split() if w.strip().isalpha()]
        return " & ".join(words) if words else keyword
