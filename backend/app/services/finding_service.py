from app.core.exceptions import NotFoundError,ValidationError
from app.models.finding_evidence import FindingEvidence
from app.models.investigation_finding import InvestigationFinding
class FindingService:
    VALID_FINDING_TYPES={"OBSERVATION","HYPOTHESIS","RECOMMENDATION","ROOT_CAUSE"}
    VALID_RELATIONSHIP_TYPES={"SUPPORTS","CONTRADICTS","CONTEXT"}
    def __init__(self,db,repository,investigation_repository,evidence_repository,finding_evidence_repository): self.db=db; self.repository=repository; self.investigation_repository=investigation_repository; self.evidence_repository=evidence_repository; self.finding_evidence_repository=finding_evidence_repository
    def get_by_id(self,finding_id):
        x=self.repository.get_by_id(finding_id)
        if x is None: raise NotFoundError("Finding not found.")
        return x
    def get_by_investigation(self,investigation_id):
        if self.investigation_repository.get_by_id(investigation_id) is None: raise NotFoundError("Investigation not found.")
        return self.repository.get_by_investigation(investigation_id)
    def create_finding(self,*,investigation_id,finding_type,finding_text,evidence_links=None):
        try:
            if self.investigation_repository.get_by_id(investigation_id) is None: raise NotFoundError("Investigation not found.")
            if finding_type not in self.VALID_FINDING_TYPES: raise ValidationError(f"Invalid finding type: {finding_type}")
            if not finding_text.strip(): raise ValidationError("Finding text cannot be empty.")
            for link in evidence_links or []:
                if link["relationship_type"] not in self.VALID_RELATIONSHIP_TYPES: raise ValidationError(f"Invalid finding/evidence relationship: {link['relationship_type']}")
                e=self.evidence_repository.get_by_id(link["evidence_id"])
                if e is None: raise NotFoundError(f"Evidence {link['evidence_id']} not found.")
                if e.investigation_id!=investigation_id: raise ValidationError("Evidence does not belong to this investigation.")
            f=InvestigationFinding(investigation_id=investigation_id,finding_type=finding_type,finding_text=finding_text.strip()); self.repository.add(f); self.db.flush()
            for link in evidence_links or []: self.finding_evidence_repository.add(FindingEvidence(finding_id=f.finding_id,evidence_id=link["evidence_id"],relationship_type=link["relationship_type"]))
            self.db.flush(); self.db.commit(); return f
        except Exception:
            self.db.rollback(); raise
