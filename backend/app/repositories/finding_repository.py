from sqlalchemy import select
from app.models.investigation_finding import InvestigationFinding
class FindingRepository:
    def __init__(self,db): self.db=db
    def get_by_id(self,finding_id): return self.db.scalars(select(InvestigationFinding).where(InvestigationFinding.finding_id==finding_id)).one_or_none()
    def get_by_investigation(self,investigation_id): return list(self.db.scalars(select(InvestigationFinding).where(InvestigationFinding.investigation_id==investigation_id).order_by(InvestigationFinding.finding_id)).all())
    def add(self,finding): self.db.add(finding); return finding
