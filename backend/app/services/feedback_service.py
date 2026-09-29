from app.core.exceptions import NotFoundError,ValidationError
from app.models.investigation_feedback import InvestigationFeedback
class FeedbackService:
    def __init__(self,db,repository,investigation_repository,user_repository): self.db=db; self.repository=repository; self.investigation_repository=investigation_repository; self.user_repository=user_repository
    def get_by_id(self,feedback_id):
        x=self.repository.get_by_id(feedback_id)
        if x is None: raise NotFoundError("Feedback not found.")
        return x
    def get_by_investigation(self,investigation_id):
        if self.investigation_repository.get_by_id(investigation_id) is None: raise NotFoundError("Investigation not found.")
        return self.repository.get_by_investigation(investigation_id)
    def get_by_user(self,user_id):
        if self.user_repository.get_by_id(user_id) is None: raise NotFoundError("User not found.")
        return self.repository.get_by_user(user_id)
    def create_feedback(self,*,investigation_id,user_id,rating,feedback_text=None):
        try:
            if rating<1 or rating>5: raise ValidationError("rating must be between 1 and 5.")
            if self.investigation_repository.get_by_id(investigation_id) is None: raise NotFoundError("Investigation not found.")
            u=self.user_repository.get_by_id(user_id)
            if u is None: raise NotFoundError("User not found.")
            if not u.is_active: raise ValidationError("Feedback user is inactive.")
            text=feedback_text.strip() if feedback_text and feedback_text.strip() else None
            f=InvestigationFeedback(investigation_id=investigation_id,user_id=user_id,rating=rating,feedback_text=text); self.repository.add(f); self.db.flush(); self.db.commit(); return f
        except Exception:
            self.db.rollback(); raise
    def get_average_rating(self,investigation_id):
        if self.investigation_repository.get_by_id(investigation_id) is None: raise NotFoundError("Investigation not found.")
        return self.repository.get_average_rating(investigation_id)
