from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.incident_event import IncidentEvent


class IncidentEventRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, event_id: int) -> IncidentEvent | None:
        statement = (
            select(IncidentEvent)
            .where(IncidentEvent.incident_event_id == event_id)
        )

        return self.db.scalars(statement).one_or_none()

    def get_by_incident(
        self,
        *,
        incident_id: int,
        before_time: datetime | None = None,
        limit: int = 50,
    ) -> list[IncidentEvent]:
        statement = (
            select(IncidentEvent)
            .where(IncidentEvent.incident_id == incident_id)
        )

        if before_time is not None:
            statement = statement.where(
                IncidentEvent.event_time <= before_time
            )

        statement = (
            statement
            .order_by(IncidentEvent.event_time.desc())
            .limit(limit)
        )

        return list(self.db.scalars(statement).all())