from app.core.exceptions import NotFoundError,ValidationError
from app.models.investigation_step import InvestigationStep
class InvestigationStepService:
    def __init__(self,db,repository,investigation_repository): self.db=db; self.repository=repository; self.investigation_repository=investigation_repository
    def get_step_by_id(self,step_id):
        x=self.repository.get_by_id(step_id)
        if x is None: raise NotFoundError("Investigation step not found.")
        return x
    def get_steps_by_investigation(self,investigation_id):
        if self.investigation_repository.get_by_id(investigation_id) is None: raise NotFoundError("Investigation not found.")
        return self.repository.get_by_investigation(investigation_id)
    def create_step(self,*,investigation_id,step_type,title,description=None,status="PENDING"):
        try:
            if self.investigation_repository.get_for_update(investigation_id) is None: raise NotFoundError("Investigation not found.")
            if not title.strip(): raise ValidationError("Investigation step title cannot be empty.")
            x=InvestigationStep(investigation_id=investigation_id,step_number=self.repository.get_next_step_number(investigation_id),step_type=step_type,title=title.strip(),description=description,status=status)
            self.repository.add(x); self.db.flush(); self.db.commit(); return x
        except Exception:
            self.db.rollback(); raise
