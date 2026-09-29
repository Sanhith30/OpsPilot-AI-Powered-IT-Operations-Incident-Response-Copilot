from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.incident import Incident
class IncidentRepository:
    def __init__(self, db: Session): self.db=db
    def get_all(self): return list(self.db.scalars(select(Incident).order_by(Incident.incident_id)).all())
    def get_by_id(self, incident_id): return self.db.scalars(select(Incident).where(Incident.incident_id==incident_id)).one_or_none()
    def get_by_number(self, incident_number): return self.db.scalars(select(Incident).where(Incident.incident_number==incident_number)).one_or_none()
    def get_by_status(self, status): return list(self.db.scalars(select(Incident).where(Incident.status==status).order_by(Incident.incident_id)).all())
