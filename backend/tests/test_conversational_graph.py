from __future__ import annotations
import pytest

from app.ai.graph.chat_graph import ConversationalChatGraph
from app.ai.providers.mock import MockLLMProvider
from app.ai.risk.heuristic import HeuristicRiskPredictor
from app.ai.tools.registry_factory import create_tool_registry
from app.repositories.deployment_repository import DeploymentRepository
from app.repositories.incident_event_repository import IncidentEventRepository
from app.repositories.incident_repository import IncidentRepository
from app.services.deployment_service import DeploymentService
from app.services.incident_event_service import IncidentEventService
from app.services.incident_service import IncidentService


@pytest.fixture
def chat_graph(db_session):
    incident_service = IncidentService(db=db_session, repository=IncidentRepository(db_session))
    deployment_service = DeploymentService(db=db_session, repository=DeploymentRepository(db_session))
    incident_event_service = IncidentEventService(db=db_session, repository=IncidentEventRepository(db_session))

    tool_registry = create_tool_registry(
        incident_service=incident_service,
        deployment_service=deployment_service,
        incident_event_service=incident_event_service,
    )

    llm_provider = MockLLMProvider()
    risk_predictor = HeuristicRiskPredictor()

    return ConversationalChatGraph(
        tool_registry=tool_registry,
        llm_provider=llm_provider,
        risk_predictor=risk_predictor,
    )


def test_chat_graph_investigates_incident(chat_graph):
    """User asks why payment API is failing -> graph selects tools and synthesizes grounded answer."""
    res = chat_graph.run(
        session_id="chat-test-001",
        user_id=1,
        query="Why is the payment API failing? Incident #1 is active.",
        incident_id=1,
    )

    assert res["session_id"] == "chat-test-001"
    assert res["answer"] is not None
    assert len(res["answer"]) > 20
    # Verify tools were selected and executed dynamically
    tool_names = [t["tool_name"] for t in res["tool_trace"]]
    assert "get_incident" in tool_names
    assert "search_incident_events" in tool_names
    assert "get_recent_deployments" in tool_names


def test_chat_graph_follow_up_deployment_question(chat_graph):
    """User asks follow-up: 'Did the latest deployment cause it?' -> graph returns causal analysis."""
    history = [
        {"role": "user", "content": "Why is payment API failing?"},
        {"role": "assistant", "content": "Connection pool timeout errors observed post-deployment."},
    ]
    res = chat_graph.run(
        session_id="chat-test-002",
        user_id=1,
        query="Did the latest deployment cause it?",
        incident_id=1,
        messages=history,
    )

    assert "deployment" in res["answer"].lower()
    tool_names = [t["tool_name"] for t in res["tool_trace"]]
    assert "get_recent_deployments" in tool_names
