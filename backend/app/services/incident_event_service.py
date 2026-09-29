from __future__ import annotations

from datetime import datetime

from app.repositories.incident_event_repository import (
    IncidentEventRepository,
)


class IncidentEventService:
    def __init__(
        self,
        db,
        repository: IncidentEventRepository,
    ):
        self.db = db
        self.repository = repository

    def get_event_by_id(self, event_id: int):
        return self.repository.get_by_id(event_id)

    def get_events_by_incident(
        self,
        *,
        incident_id: int,
        before_time: datetime | None = None,
        limit: int = 50,
    ):
        return self.repository.get_by_incident(
            incident_id=incident_id,
            before_time=before_time,
            limit=limit,
        )