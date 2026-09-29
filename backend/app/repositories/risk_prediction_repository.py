from sqlalchemy import select
from app.models.risk_prediction import RiskPrediction
class RiskPredictionRepository:
    def __init__(self,db): self.db=db
    def get_by_id(self,prediction_id): return self.db.scalars(select(RiskPrediction).where(RiskPrediction.prediction_id==prediction_id)).one_or_none()
    def get_by_investigation(self,investigation_id): return list(self.db.scalars(select(RiskPrediction).where(RiskPrediction.investigation_id==investigation_id).order_by(RiskPrediction.prediction_id)).all())
    def get_latest_by_investigation(self, investigation_id: int):
        return self.db.scalars(
            select(RiskPrediction)
            .where(RiskPrediction.investigation_id == investigation_id)
            .order_by(RiskPrediction.predicted_at.desc())
        ).first()
    def get_by_incident(self,incident_id): return list(self.db.scalars(select(RiskPrediction).where(RiskPrediction.incident_id==incident_id).order_by(RiskPrediction.prediction_id)).all())
    def add(self,prediction): self.db.add(prediction); return prediction
