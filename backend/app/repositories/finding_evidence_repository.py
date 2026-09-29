from sqlalchemy import select
from app.models.finding_evidence import FindingEvidence
class FindingEvidenceRepository:
    def __init__(self,db): self.db=db
    def add(self,link): self.db.add(link); return link
    def get_by_finding(self,finding_id): return list(self.db.scalars(select(FindingEvidence).where(FindingEvidence.finding_id==finding_id).order_by(FindingEvidence.evidence_id)).all())
    def get_by_evidence(self,evidence_id): return list(self.db.scalars(select(FindingEvidence).where(FindingEvidence.evidence_id==evidence_id).order_by(FindingEvidence.finding_id)).all())
