from decimal import Decimal

from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.incident_repository import IncidentRepository
from app.repositories.investigation_repository import InvestigationRepository
from app.repositories.user_repository import UserRepository
from app.services.audit_log_service import AuditLogService
from app.services.investigation_service import InvestigationService


class FakeGraph:
    class GraphWrapper:
        def invoke(self, state):
            return {
                "status": "COMPLETED",
                "current_stage": "completed",
                "final_summary": "Payment API incident resolved through investigation.",
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
                    "model_name": "incident_escalation_model",
                    "model_version": "1.0.0",
                    "risk_score": 0.85,
                    "risk_level": "HIGH",
                    "prediction_type": "INCIDENT_ESCALATION",
                    "prediction_explanation": "High severity with recent deployment.",
                    "factors": {"has_recent_deployment": True},
                },
            }

    graph = GraphWrapper()


def test_service_run_investigation_persists_full_lifecycle(db_session):
    inv_repo = InvestigationRepository(db_session)
    inc_repo = IncidentRepository(db_session)
    user_repo = UserRepository(db_session)
    audit_repo = AuditLogRepository(db_session)
    audit_service = AuditLogService(db_session, audit_repo, user_repo)

    service = InvestigationService(db_session, inv_repo, inc_repo, audit_service)

    detail = service.run_investigation(
        incident_id=1,
        question="What caused the payment outage?",
        actor_user_id=1,
        graph=FakeGraph(),
    )

    assert detail is not None
    assert detail.status == "COMPLETED"
    assert "Payment API incident resolved" in detail.final_summary
    assert len(detail.tool_calls) == 1
    assert len(detail.evidence) == 1
    assert detail.evidence[0].evidence_type == "deployment"
    assert len(detail.findings) == 1
    assert detail.findings[0].finding_type == "HIGH"
    assert len(detail.findings[0].evidence_links) == 1
    assert len(detail.risk_predictions) == 1
    assert detail.risk_predictions[0].risk_level == "HIGH"
