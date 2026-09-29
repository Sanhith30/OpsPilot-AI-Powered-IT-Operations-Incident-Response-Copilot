from decimal import Decimal
from sqlalchemy import select

from app.models.investigation import Investigation
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.incident_repository import IncidentRepository
from app.repositories.investigation_repository import InvestigationRepository
from app.repositories.risk_prediction_repository import RiskPredictionRepository
from app.repositories.user_repository import UserRepository
from app.services.audit_log_service import AuditLogService
from app.services.investigation_service import InvestigationService
from app.services.risk_prediction_service import RiskPredictionService


class FakeInvestigationGraph:
    class GraphWrapper:
        def invoke(self, state):
            return {
                "status": "COMPLETED",
                "current_stage": "risk_predicted",
                "final_summary": "Payment API incident analyzed with high risk.",
                "tool_results": [
                    {
                        "tool_name": "get_incident",
                        "status": "SUCCESS",
                        "data": {"incident_number": "INC-1042"},
                    }
                ],
                "evidence": [
                    {
                        "source_type": "deployment",
                        "source_id": "3",
                        "title": "Deployment 2.8.1",
                        "content": "Deployment completed",
                        "metadata": {"version": "2.8.1"},
                    }
                ],
                "findings": [
                    {
                        "finding": "Deployment 2.8.1 occurred right before the incident.",
                        "confidence": "HIGH",
                        "evidence_refs": [{"source_type": "deployment", "source_id": "3"}],
                    }
                ],
                "risk_prediction": {
                    "model_name": "incident_risk_baseline",
                    "model_version": "1.0.0",
                    "risk_score": Decimal("0.70"),
                    "risk_level": "HIGH",
                    "features": {
                        "severity": "HIGH",
                        "status": "INVESTIGATING",
                        "event_count": 5,
                        "timeout_count": 1,
                        "error_rate_percent": 13.7,
                        "recent_deployment": True,
                    },
                    "explanation": "High incident severity. A timeout-related event was observed.",
                },
            }

    graph = GraphWrapper()


def test_existing_investigation_is_reused(db_session):
    inv_repo = InvestigationRepository(db_session)
    inc_repo = IncidentRepository(db_session)
    user_repo = UserRepository(db_session)
    audit_repo = AuditLogRepository(db_session)
    audit_service = AuditLogService(db_session, audit_repo, user_repo)
    risk_repo = RiskPredictionRepository(db_session)
    risk_service = RiskPredictionService(db_session, risk_repo)

    service = InvestigationService(
        db=db_session,
        repository=inv_repo,
        incident_repository=inc_repo,
        audit_log_service=audit_service,
        risk_prediction_service=risk_service,
    )

    investigation = service.create_investigation(
        incident_id=1,
        investigation_type="ASSISTED",
        question="Why is the Payment API failing?",
        actor_user_id=4,
    )

    original_id = investigation.investigation_id
    assert investigation.status == "STARTED"

    result = service.run_investigation(
        incident_id=1,
        question="Why is the Payment API failing?",
        actor_user_id=4,
        investigation_type="ASSISTED",
        investigation_id=original_id,
        graph=FakeInvestigationGraph(),
    )

    assert result.investigation_id == original_id
    assert result.status == "COMPLETED"
    assert result.completed_at is not None

    rows = inv_repo.get_by_incident(1)
    matching = [item for item in rows if item.investigation_id == original_id]
    assert len(matching) == 1
    assert matching[0].status == "COMPLETED"
