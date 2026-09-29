from sqlalchemy import func, select
from app.models.investigation_feedback import InvestigationFeedback
class FeedbackRepository:
    def __init__(self,db): self.db=db
    def get_by_id(self,feedback_id): return self.db.scalars(select(InvestigationFeedback).where(InvestigationFeedback.feedback_id==feedback_id)).one_or_none()
    def get_by_investigation(self,investigation_id): return list(self.db.scalars(select(InvestigationFeedback).where(InvestigationFeedback.investigation_id==investigation_id).order_by(InvestigationFeedback.feedback_id)).all())
    def get_by_user(self,user_id): return list(self.db.scalars(select(InvestigationFeedback).where(InvestigationFeedback.user_id==user_id).order_by(InvestigationFeedback.feedback_id)).all())
    def get_average_rating(self,investigation_id):
        value=self.db.scalar(select(func.avg(InvestigationFeedback.rating)).where(InvestigationFeedback.investigation_id==investigation_id)); return float(value) if value is not None else None
    def add(self,feedback): self.db.add(feedback); return feedback
