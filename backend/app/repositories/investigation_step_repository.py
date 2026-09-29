from sqlalchemy import func, select
from app.models.investigation_step import InvestigationStep
class InvestigationStepRepository:
    def __init__(self, db): self.db=db
    def get_by_id(self,step_id): return self.db.scalars(select(InvestigationStep).where(InvestigationStep.step_id==step_id)).one_or_none()
    def get_by_investigation(self,investigation_id): return list(self.db.scalars(select(InvestigationStep).where(InvestigationStep.investigation_id==investigation_id).order_by(InvestigationStep.step_number)).all())
    def get_next_step_number(self,investigation_id):
        n=self.db.scalar(select(func.coalesce(func.max(InvestigationStep.step_number),0)).where(InvestigationStep.investigation_id==investigation_id)); return int(n)+1
    def add(self,step): self.db.add(step); return step
