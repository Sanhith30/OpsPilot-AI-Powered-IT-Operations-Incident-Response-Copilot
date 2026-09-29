from datetime import datetime,timezone
from app.core.exceptions import NotFoundError,ValidationError
from app.models.investigation_evidence import InvestigationEvidence
class EvidenceService:
    def __init__(self,db,repository,investigation_repository,tool_call_repository): self.db=db; self.repository=repository; self.investigation_repository=investigation_repository; self.tool_call_repository=tool_call_repository
    def get_by_id(self,evidence_id):
        x=self.repository.get_by_id(evidence_id)
        if x is None: raise NotFoundError("Evidence not found.")
        return x
    def get_by_investigation(self,investigation_id):
        if self.investigation_repository.get_by_id(investigation_id) is None: raise NotFoundError("Investigation not found.")
        return self.repository.get_by_investigation(investigation_id)
    def get_by_tool_call(self,tool_call_id):
        if self.tool_call_repository.get_by_id(tool_call_id) is None: raise NotFoundError("Tool call not found.")
        return self.repository.get_by_tool_call(tool_call_id)
    def create_evidence(self,*,investigation_id,evidence_type,source,content,source_reference=None,tool_call_id=None,metadata=None):
        try:
            if self.investigation_repository.get_by_id(investigation_id) is None: raise NotFoundError("Investigation not found.")
            if not source.strip() or not content.strip(): raise ValidationError("Evidence source and content cannot be empty.")
            if tool_call_id is not None:
                t=self.tool_call_repository.get_by_id(tool_call_id)
                if t is None: raise NotFoundError("Tool call not found.")
                if t.investigation_id!=investigation_id: raise ValidationError("Tool call does not belong to this investigation.")
            x=InvestigationEvidence(investigation_id=investigation_id,tool_call_id=tool_call_id,evidence_type=evidence_type,source=source.strip(),source_reference=source_reference,content=content.strip(),evidence_metadata=metadata,collected_at=datetime.now(timezone.utc)); self.repository.add(x); self.db.flush(); self.db.commit(); return x
        except Exception:
            self.db.rollback(); raise
