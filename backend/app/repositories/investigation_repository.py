from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.finding_evidence import FindingEvidence
from app.models.investigation import Investigation
from app.models.investigation_step import InvestigationStep
from app.models.investigation_evidence import InvestigationEvidence
from app.models.investigation_finding import InvestigationFinding
class InvestigationRepository:
    def __init__(self, db): self.db=db
    def get_all(self): return list(self.db.scalars(select(Investigation).order_by(Investigation.investigation_id)).all())
    def get_by_id(self,investigation_id): return self.db.scalars(select(Investigation).where(Investigation.investigation_id==investigation_id)).one_or_none()
    def get_by_incident(self,incident_id): return list(self.db.scalars(select(Investigation).where(Investigation.incident_id==incident_id).order_by(Investigation.investigation_id)).all())
    def get_by_status(self,status): return list(self.db.scalars(select(Investigation).where(Investigation.status==status).order_by(Investigation.investigation_id)).all())
    def get_by_id_with_details(self,investigation_id):
        q=(select(Investigation).where(Investigation.investigation_id==investigation_id).options(
            selectinload(Investigation.steps).selectinload(InvestigationStep.tool_calls),
            selectinload(Investigation.tool_calls),
            selectinload(Investigation.evidence).selectinload(InvestigationEvidence.finding_links),
            selectinload(Investigation.findings).selectinload(InvestigationFinding.evidence_links).selectinload(FindingEvidence.evidence),
            selectinload(Investigation.risk_predictions),
            selectinload(Investigation.feedback)))
        return self.db.scalars(q).one_or_none()
    def get_for_update(self,investigation_id): return self.db.scalars(select(Investigation).where(Investigation.investigation_id==investigation_id).with_for_update()).one_or_none()
    def add(self,investigation): self.db.add(investigation); return investigation
