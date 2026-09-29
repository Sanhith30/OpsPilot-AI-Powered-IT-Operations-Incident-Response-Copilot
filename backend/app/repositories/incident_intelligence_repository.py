from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.incident_intelligence import IncidentIntelligence


class IncidentIntelligenceRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, intelligence_id: int) -> IncidentIntelligence | None:
        return self.db.scalars(
            select(IncidentIntelligence).where(
                IncidentIntelligence.intelligence_id == intelligence_id
            )
        ).one_or_none()

    def get_latest_by_incident(self, incident_id: int) -> IncidentIntelligence | None:
        return self.db.scalars(
            select(IncidentIntelligence)
            .where(IncidentIntelligence.incident_id == incident_id)
            .order_by(IncidentIntelligence.created_at.desc())
        ).first()

    def get_latest_by_investigation(self, investigation_id: int) -> IncidentIntelligence | None:
        return self.db.scalars(
            select(IncidentIntelligence)
            .where(IncidentIntelligence.investigation_id == investigation_id)
            .order_by(IncidentIntelligence.created_at.desc())
        ).first()

    def get_by_investigation(self, investigation_id: int) -> list[IncidentIntelligence]:
        return list(
            self.db.scalars(
                select(IncidentIntelligence)
                .where(IncidentIntelligence.investigation_id == investigation_id)
                .order_by(IncidentIntelligence.created_at.desc())
            ).all()
        )

    def get_by_incident(self, incident_id: int) -> list[IncidentIntelligence]:
        return list(
            self.db.scalars(
                select(IncidentIntelligence)
                .where(IncidentIntelligence.incident_id == incident_id)
                .order_by(IncidentIntelligence.created_at.desc())
            ).all()
        )

    def add(self, intelligence: IncidentIntelligence) -> IncidentIntelligence:
        self.db.add(intelligence)
        self.db.flush()
        return intelligence
