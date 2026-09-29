from app.ai.graph.investigation_graph import InvestigationGraph
from app.ai.providers.config import LLMConfig
from app.ai.providers.factory import create_llm_provider
from app.ai.tools.registry_factory import create_tool_registry

from app.core.config import settings
from app.db.session import SessionLocal

from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.deployment_repository import DeploymentRepository
from app.repositories.incident_event_repository import IncidentEventRepository
from app.repositories.incident_repository import IncidentRepository
from app.repositories.investigation_repository import InvestigationRepository
from app.repositories.risk_prediction_repository import RiskPredictionRepository
from app.repositories.user_repository import UserRepository

from app.services.audit_log_service import AuditLogService
from app.services.deployment_service import DeploymentService
from app.services.incident_event_service import IncidentEventService
from app.services.incident_service import IncidentService
from app.services.investigation_service import InvestigationService
from app.services.risk_prediction_service import RiskPredictionService


INCIDENT_ID = 1


def main() -> None:
    db = SessionLocal()

    try:
        # -------------------------------------------------
        # 1. Build real application services
        # -------------------------------------------------
        incident_repository = IncidentRepository(db)
        deployment_repository = DeploymentRepository(db)
        incident_event_repository = IncidentEventRepository(db)
        investigation_repository = InvestigationRepository(db)
        user_repository = UserRepository(db)
        audit_log_repository = AuditLogRepository(db)
        risk_prediction_repository = RiskPredictionRepository(db)

        incident_service = IncidentService(
            db,
            incident_repository,
        )

        deployment_service = DeploymentService(
            db,
            deployment_repository,
        )

        incident_event_service = IncidentEventService(
            db=db,
            repository=incident_event_repository,
        )

        audit_log_service = AuditLogService(
            db=db,
            repository=audit_log_repository,
            user_repository=user_repository,
        )

        risk_prediction_service = RiskPredictionService(
            db=db,
            repository=risk_prediction_repository,
            incident_repository=incident_repository,
            investigation_repository=investigation_repository,
        )

        investigation_service = InvestigationService(
            db=db,
            repository=investigation_repository,
            incident_repository=incident_repository,
            audit_log_service=audit_log_service,
            risk_prediction_service=risk_prediction_service,
        )

        # -------------------------------------------------
        # 2. Build real AI tool registry
        # -------------------------------------------------
        registry = create_tool_registry(
            incident_service=incident_service,
            deployment_service=deployment_service,
            incident_event_service=incident_event_service,
        )

        # -------------------------------------------------
        # 3. Build Gemini provider
        # -------------------------------------------------
        config = LLMConfig(
            provider=settings.llm_provider,
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            timeout_seconds=settings.llm_timeout_seconds,
            api_key=settings.gemini_api_key,
        )

        llm_provider = create_llm_provider(config)

        # -------------------------------------------------
        # 4. Build LangGraph
        # -------------------------------------------------
        graph = InvestigationGraph(
            tool_registry=registry,
            llm_provider=llm_provider,
        )

        # -------------------------------------------------
        # 5. Run and persist the full investigation lifecycle
        # -------------------------------------------------
        investigation = investigation_service.run_investigation(
            incident_id=INCIDENT_ID,
            question=(
                "Why is this incident happening? "
                "What evidence suggests the most likely cause, "
                "and what should the operations engineer check next?"
            ),
            actor_user_id=1,
            investigation_type="ASSISTED",
            graph=graph,
        )

        # -------------------------------------------------
        # 6. Print persisted results from PostgreSQL
        # -------------------------------------------------
        print("\n==============================")
        print("OPS PILOT PERSISTED INVESTIGATION")
        print("==============================")

        print("Investigation ID:", investigation.investigation_id)
        print("Incident ID:", investigation.incident_id)
        print("Status:", investigation.status)
        print("Started At:", investigation.started_at)
        print("Completed At:", investigation.completed_at)

        print("\nFinal Summary:")
        print(investigation.final_summary)

        print(f"\nPersisted Tool Calls ({len(investigation.tool_calls)}):")
        for tc in investigation.tool_calls:
            print(f"  - [{tc.status}] {tc.tool_name} (id={tc.tool_call_id})")

        print(f"\nPersisted Evidence ({len(investigation.evidence)}):")
        for ev in investigation.evidence:
            print(f"  - [{ev.evidence_type}] {ev.source} (id={ev.evidence_id}, ref={ev.source_reference})")

        print(f"\nPersisted Findings ({len(investigation.findings)}):")
        for f in investigation.findings:
            refs = [f"ev_id={link.evidence_id}" for link in f.evidence_links]
            print(f"  - [{f.finding_type}] {f.finding_text} (links: {', '.join(refs)})")

        print(f"\nPersisted Risk Predictions ({len(investigation.risk_predictions)}):")
        for rp in investigation.risk_predictions:
            print(f"  - Model: {rp.model_name} v{rp.model_version}")
            print(f"    Type: {rp.prediction_type}")
            print(f"    Score: {rp.risk_score}")
            print(f"    Level: {rp.risk_level}")
            print(f"    Features: {rp.prediction_metadata}")
            print(f"    Explanation: {rp.prediction_explanation}")
            print(f"    Predicted At: {rp.predicted_at}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
