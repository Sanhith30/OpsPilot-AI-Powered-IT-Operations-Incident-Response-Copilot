from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.service_metric import ServiceMetric


class ServiceMetricRepository:
    """
    Data-access layer for core.service_metrics.
    Supports time-range queries, per-service aggregation, and metric-name filtering.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, metric: ServiceMetric) -> ServiceMetric:
        self.db.add(metric)
        return metric

    def get_for_service(
        self,
        *,
        service_id: int,
        metric_name: Optional[str] = None,
        from_time: Optional[datetime] = None,
        to_time: Optional[datetime] = None,
        environment: Optional[str] = None,
        limit: int = 100,
    ) -> List[ServiceMetric]:
        q = self.db.query(ServiceMetric).filter(ServiceMetric.service_id == service_id)

        if metric_name:
            q = q.filter(ServiceMetric.metric_name == metric_name)

        if environment:
            q = q.filter(ServiceMetric.environment == environment)

        if from_time:
            q = q.filter(ServiceMetric.recorded_at >= from_time)

        if to_time:
            q = q.filter(ServiceMetric.recorded_at <= to_time)

        return q.order_by(ServiceMetric.recorded_at.desc()).limit(limit).all()

    def get_latest_by_service(
        self,
        *,
        service_id: int,
        environment: Optional[str] = None,
        limit: int = 20,
    ) -> List[ServiceMetric]:
        """Return the most recent metric snapshots across all metric names."""
        q = (
            self.db.query(ServiceMetric)
            .filter(ServiceMetric.service_id == service_id)
        )
        if environment:
            q = q.filter(ServiceMetric.environment == environment)

        return q.order_by(ServiceMetric.recorded_at.desc()).limit(limit).all()

    def get_by_service_name(
        self,
        *,
        service_name: str,
        metric_name: Optional[str] = None,
        from_time: Optional[datetime] = None,
        limit: int = 50,
    ) -> List[ServiceMetric]:
        q = (
            self.db.query(ServiceMetric)
            .filter(ServiceMetric.service_name.ilike(f"%{service_name}%"))
        )
        if metric_name:
            q = q.filter(ServiceMetric.metric_name == metric_name)
        if from_time:
            q = q.filter(ServiceMetric.recorded_at >= from_time)

        return q.order_by(ServiceMetric.recorded_at.desc()).limit(limit).all()
