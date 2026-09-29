"""
End-to-end smoke test: InvestigationGraph with live GeminiProvider
"""
from datetime import datetime, timezone
import json

from app.core.config import settings
from app.ai.graph.investigation_graph import InvestigationGraph
from app.ai.providers.gemini import GeminiProvider
from app.ai.state.factory import create_initial_investigation_state
from app.ai.tools.registry_factory import create_tool_registry


class FakeIncident:
    incident_id = 1
    incident_number = "INC-1042"
    service_id = 1
    title = "Payment API elevated error rate"
    description = "Payment API is experiencing elevated 500 internal server errors."
    severity = "HIGH"
    status = "INVESTIGATING"
    started_at = datetime(2026, 9, 26, 9, 20, tzinfo=timezone.utc)
    detected_at = datetime(2026, 9, 26, 9, 24, tzinfo=timezone.utc)
    resolved_at = None
    assigned_team_id = 1
    assigned_user_id = 2
    impact_summary = "Payment checkout failures affecting 35% of customer transactions."
    root_cause = None


class FakeIncidentService:
    def get_incident_by_id(self, incident_id):
        return FakeIncident()


class FakeDeployment:
    deployment_id = 3
    service_id = 1
    version = "2.8.1"
    environment = "production"
    commit_hash = "f8a91b2"
    deployment_type = "STANDARD"
    trigger_type = "MANUAL"
    status = "SUCCESS"
    started_at = datetime(2026, 9, 26, 9, 10, tzinfo=timezone.utc)
    completed_at = datetime(2026, 9, 26, 9, 15, tzinfo=timezone.utc)
    deployed_by = 4


class FakeDeploymentService:
    def get_recent_deployments(self, *, service_id, environment, before_time, limit):
        return [FakeDeployment()]


class FakeIncidentEvent:
    incident_event_id = 101
    incident_id = 1
    event_type = "ALERT_FIRED"
    description = "High error rate alert triggered on payments-gateway service: HTTP 500 rate > 5%"
    event_time = datetime(2026, 9, 26, 9, 20, tzinfo=timezone.utc)
    created_by = 1
    event_metadata = {"service": "payments-gateway", "metric": "http_5xx_rate", "value": 0.08}



class FakeIncidentEventService:
    def get_events_by_incident(self, *, incident_id, before_time=None, limit=50):
        return [FakeIncidentEvent()]


def main():
    model_name = "gemini-2.5-flash"
    print(f"Connecting to Gemini ({model_name})...")
    registry = create_tool_registry(
        incident_service=FakeIncidentService(),
        deployment_service=FakeDeploymentService(),
        incident_event_service=FakeIncidentEventService(),
    )

    from app.ai.providers.config import LLMConfig
    from app.ai.providers.factory import create_llm_provider

    config = LLMConfig(
        provider="gemini",
        model=settings.llm_model,
        timeout_seconds=settings.llm_timeout_seconds,
        api_key=settings.gemini_api_key,
    )

    provider = create_llm_provider(config)

    graph = InvestigationGraph(
        tool_registry=registry,
        llm_provider=provider,
    )

    state = create_initial_investigation_state(
        incident_id=1,
        user_question="What caused the Payment API error rate spike?",
    )

    result = graph.graph.invoke(state)

    print("\nInvestigation Status:", result["status"])
    print("Current Stage:", result["current_stage"])
    print("\n--- Final Summary ---")
    print(result.get("final_summary"))
    print("\n--- Findings ---")
    print(json.dumps(result.get("findings"), indent=2))
    if result.get("errors"):
        print("\n--- Errors ---")
        print(result["errors"])


if __name__ == "__main__":
    main()

