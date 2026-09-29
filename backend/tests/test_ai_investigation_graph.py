from datetime import datetime, timezone

from app.ai.graph.investigation_graph import InvestigationGraph
from app.ai.state.factory import (
    create_initial_investigation_state,
)
from app.ai.tools.registry_factory import create_tool_registry


class FakeIncident:
    incident_id = 1
    incident_number = "INC-1042"
    service_id = 1
    title = "Payment API elevated error rate"
    description = "Payment API is experiencing elevated errors."
    severity = "HIGH"
    status = "INVESTIGATING"

    started_at = datetime(
        2026,
        9,
        26,
        9,
        20,
        tzinfo=timezone.utc,
    )

    detected_at = datetime(
        2026,
        9,
        26,
        9,
        24,
        tzinfo=timezone.utc,
    )

    resolved_at = None
    assigned_team_id = 1
    assigned_user_id = 2
    impact_summary = "Payment failures affecting customers."
    root_cause = None


class FakeIncidentService:

    def get_incident_by_id(self, incident_id):
        assert incident_id == 1
        return FakeIncident()


class FakeDeployment:
    deployment_id = 3
    service_id = 1
    version = "2.8.1"
    environment = "production"
    commit_hash = "abc123"
    deployment_type = "STANDARD"
    trigger_type = "MANUAL"
    status = "SUCCESS"

    started_at = datetime(
        2026,
        9,
        26,
        9,
        15,
        tzinfo=timezone.utc,
    )

    completed_at = datetime(
        2026,
        9,
        26,
        9,
        20,
        tzinfo=timezone.utc,
    )

    deployed_by = 4


class FakeDeploymentService:

    def get_recent_deployments(
        self,
        *,
        service_id,
        environment,
        before_time,
        limit,
    ):
        assert service_id == 1
        assert environment == "production"
        assert limit == 5

        return [FakeDeployment()]


class FakeIncidentEventService:

    def get_events_by_incident(
        self,
        *,
        incident_id,
        before_time=None,
        limit=50,
    ):
        return []


class FakeLLMProvider:

    def generate(
        self,
        *,
        system_prompt,
        user_prompt,
        temperature=0.0,
        metadata=None,
        response_schema=None,
        **kwargs,
    ):
        return """
        {
          "summary": "The incident occurred after a production change.",
          "findings": [
            {
              "finding": "A recent deployment is temporally associated with the incident.",
              "confidence": "HIGH",
              "evidence_refs": [
                {
                  "source_type": "deployment",
                  "source_id": "3"
                }
              ]
            }
          ],
          "probable_root_cause": "A deployment-related regression is possible.",
          "recommendations": [
            "Review the changes included in deployment 3."
          ]
        }
        """


def test_langgraph_success_path():

    registry = create_tool_registry(
        incident_service=FakeIncidentService(),
        deployment_service=FakeDeploymentService(),
        incident_event_service=FakeIncidentEventService(),
    )

    graph = InvestigationGraph(
        tool_registry=registry,
        llm_provider=FakeLLMProvider(),
    )

    state = create_initial_investigation_state(
        incident_id=1,
        user_question="Why is Payment API failing?",
    )

    result = graph.graph.invoke(state)

    assert result["incident_id"] == 1
    assert result["status"] == "COMPLETED"
    assert result["current_stage"] == "completed"

    tool_names = [
        r["tool_name"]
        for r in result["tool_results"]
    ]

    assert "get_incident" in tool_names
    assert "get_recent_deployments" in tool_names
    assert "search_incident_events" in tool_names

    assert result["final_summary"] != ""
    assert len(result["findings"]) == 1
    assert result["findings"][0]["confidence"] == "HIGH"

    deployments = next(
        r for r in result["tool_results"]
        if r["tool_name"] == "get_recent_deployments"
    )["data"]["deployments"]

    assert len(deployments) == 1
    assert deployments[0]["version"] == "2.8.1"

    evidence_types = [e["source_type"] for e in result["evidence"]]
    assert "deployment" in evidence_types
    deployment_evidence = next(
        e for e in result["evidence"]
        if e["source_type"] == "deployment"
    )
    assert deployment_evidence["source_id"] == "3"
    assert "2.8.1" in deployment_evidence["title"]

    assert result["risk_prediction"] is not None
    assert result["risk_prediction"]["model_name"] == "incident_risk_baseline"
    assert float(result["risk_prediction"]["risk_score"]) > 0
    assert result["risk_prediction"]["risk_level"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")




class FailingIncidentService:

    def get_incident_by_id(self, incident_id):
        raise Exception(
            "Simulated incident retrieval failure."
        )


def test_langgraph_incident_failure_path():

    registry = create_tool_registry(
        incident_service=FailingIncidentService(),
        deployment_service=FakeDeploymentService(),
        incident_event_service=FakeIncidentEventService(),
    )

    graph = InvestigationGraph(
        tool_registry=registry,
        llm_provider=FakeLLMProvider(),
    )

    state = create_initial_investigation_state(
        incident_id=1,
        user_question="Why is Payment API failing?",
    )

    result = graph.graph.invoke(state)

    assert result["status"] == "FAILED"
    assert (
        result["current_stage"]
        == "investigation_failed"
    )

    assert len(result["tool_results"]) == 1
    assert len(result["errors"]) == 1


class FailingDeploymentService:

    def get_recent_deployments(
        self,
        *,
        service_id,
        environment,
        before_time,
        limit,
    ):
        raise Exception(
            "Simulated deployment service failure."
        )


def test_langgraph_deployment_failure_is_non_fatal():

    registry = create_tool_registry(
        incident_service=FakeIncidentService(),
        deployment_service=FailingDeploymentService(),
        incident_event_service=FakeIncidentEventService(),
    )

    graph = InvestigationGraph(
        tool_registry=registry,
        llm_provider=FakeLLMProvider(),
    )

    state = create_initial_investigation_state(
        incident_id=1,
        user_question="Why is Payment API failing?",
    )

    result = graph.graph.invoke(state)

    assert result["status"] == "COMPLETED"
    assert result["current_stage"] == "completed"

    tool_names = [
        r["tool_name"]
        for r in result["tool_results"]
    ]

    assert "get_recent_deployments" in tool_names
    assert "search_incident_events" in tool_names

    deployment_result = next(
        r for r in result["tool_results"]
        if r["tool_name"] == "get_recent_deployments"
    )
    assert deployment_result["status"] == "FAILED"

    assert len(result["errors"]) == 1
    assert (
        result["errors"][0]["stage"]
        == "loading_deployments"
    )


class FailingIncidentEventService:

    def get_events_by_incident(
        self,
        *,
        incident_id,
        before_time=None,
        limit=50,
    ):
        raise TimeoutError(
            "incident event service unavailable"
        )


def test_langgraph_incident_event_failure_is_non_fatal():

    registry = create_tool_registry(
        incident_service=FakeIncidentService(),
        deployment_service=FakeDeploymentService(),
        incident_event_service=FailingIncidentEventService(),
    )

    graph = InvestigationGraph(
        tool_registry=registry,
        llm_provider=FakeLLMProvider(),
    )

    state = create_initial_investigation_state(
        incident_id=1,
        user_question="Why did this incident happen?",
    )

    result = graph.graph.invoke(state)

    assert result["status"] == "COMPLETED"
    assert result["current_stage"] == "completed"

    assert any(
        error["stage"] == "load_incident_events"
        for error in result["errors"]
    )


class FailingLLMProvider:

    def generate(
        self,
        *,
        system_prompt,
        user_prompt,
        temperature=0.0,
        metadata=None,
        response_schema=None,
        **kwargs,
    ):
        raise TimeoutError("provider timeout")


def test_langgraph_llm_failure_is_non_fatal_to_process_but_fails_investigation():

    registry = create_tool_registry(
        incident_service=FakeIncidentService(),
        deployment_service=FakeDeploymentService(),
        incident_event_service=FakeIncidentEventService(),
    )

    graph = InvestigationGraph(
        tool_registry=registry,
        llm_provider=FailingLLMProvider(),
    )

    state = create_initial_investigation_state(
        incident_id=1,
        user_question="Why did the incident happen?",
    )

    result = graph.graph.invoke(state)

    assert result["status"] == "FAILED"
    assert result["current_stage"] == "analysis"

    assert any(
        error["error_code"] == "LLM_ANALYSIS_FAILED"
        for error in result["errors"]
    )


def test_langgraph_produces_risk_prediction():

    registry = create_tool_registry(
        incident_service=FakeIncidentService(),
        deployment_service=FakeDeploymentService(),
        incident_event_service=FakeIncidentEventService(),
    )

    graph = InvestigationGraph(
        tool_registry=registry,
        llm_provider=FakeLLMProvider(),
    )

    state = create_initial_investigation_state(
        incident_id=1,
        user_question="Why is Payment API failing?",
    )

    result = graph.graph.invoke(state)

    assert result["status"] == "COMPLETED"
    assert result["risk_prediction"] is not None

    prediction = result["risk_prediction"]

    assert "risk_score" in prediction
    assert "risk_level" in prediction
    assert "model_name" in prediction
    assert "model_version" in prediction
    assert "features" in prediction
    assert "explanation" in prediction

# ============================================================
# RAG integration tests (Step 17.9)
# ============================================================


def test_rag_skipped_gracefully_when_tool_not_registered():
    """
    When search_knowledge is not in the registry the investigation
    must still complete.  rag_query must be None (clean skip) and
    rag_context must remain None.
    """

    registry = create_tool_registry(
        incident_service=FakeIncidentService(),
        deployment_service=FakeDeploymentService(),
        incident_event_service=FakeIncidentEventService(),
        # knowledge_retrieval_service intentionally omitted
    )

    graph = InvestigationGraph(
        tool_registry=registry,
        llm_provider=FakeLLMProvider(),
    )

    state = create_initial_investigation_state(
        incident_id=1,
        user_question="Why is Payment API failing?",
    )

    result = graph.graph.invoke(state)

    assert result["status"] == "COMPLETED"
    assert result["current_stage"] == "completed"
    assert result["rag_query"] is None
    assert result["rag_context"] is None
    assert result["rag_citations"] == []


# --------------- helpers for RAG retrieval tests -------------


class _FakeRetrievalResponse:
    """Minimal stand-in for the object returned by the retrieval service."""

    def __init__(self, results):
        from app.ai.rag.retrieval.schemas import RetrievalFilters

        self.query = "test query"
        self.results = results
        self.result_count = len(results)
        self.applied_filters = RetrievalFilters()

    def model_dump(self, *, mode="python"):
        return {
            "query": self.query,
            "results": [
                r.model_dump(mode=mode) for r in self.results
            ],
            "result_count": self.result_count,
            "applied_filters": self.applied_filters.model_dump(
                mode=mode
            ),
        }


class FakeKnowledgeRetrievalService:
    """Returns a single canned RetrievalResult."""

    def retrieve(self, query_obj, *, context):
        from app.ai.rag.schemas import RetrievalResult

        result = RetrievalResult(
            chunk_id="chunk-001",
            document_id="doc-001",
            content=(
                "Check connection pool settings when "
                "Payment API shows timeouts."
            ),
            score=0.87,
            metadata={
                "source_type": "runbook",
                "source_name": "payment-api-timeouts.md",
                "title": "Payment API Timeout Runbook",
                "version_number": 2,
                "document_id": "doc-001",
            },
        )
        return _FakeRetrievalResponse([result])


class FailingKnowledgeRetrievalService:
    """Simulates a vector-store outage."""

    def retrieve(self, query_obj, *, context):
        raise TimeoutError("vector-store unavailable")


# --------------- actual tests --------------------------------


def test_rag_context_populated_when_retrieval_succeeds():
    """
    When search_knowledge is registered and returns results the
    investigation must complete with rag_context set and at least
    one citation present.
    """
    from app.ai.rag.access.policy import KnowledgeAccessContext

    access_context = KnowledgeAccessContext(user_id=1, team_id=None)

    registry = create_tool_registry(
        incident_service=FakeIncidentService(),
        deployment_service=FakeDeploymentService(),
        incident_event_service=FakeIncidentEventService(),
        knowledge_retrieval_service=FakeKnowledgeRetrievalService(),
        knowledge_access_context=access_context,
    )

    graph = InvestigationGraph(
        tool_registry=registry,
        llm_provider=FakeLLMProvider(),
    )

    state = create_initial_investigation_state(
        incident_id=1,
        user_question="Why is Payment API failing?",
    )

    result = graph.graph.invoke(state)

    assert result["status"] == "COMPLETED"
    assert result["current_stage"] == "completed"

    # RAG query must include both incident title and user question
    assert result["rag_query"] is not None
    assert "Payment API" in result["rag_query"]

    # Context must be an LLM-ready string containing the chunk content
    assert result["rag_context"] is not None
    assert "connection pool" in result["rag_context"]

    # Citation mapping must contain at least one entry
    assert len(result["rag_citations"]) >= 1
    first = result["rag_citations"][0]
    assert first["citation_id"] == "KB-1"
    assert first["chunk_id"] == "chunk-001"

    # search_knowledge result must appear in tool_results
    tool_names = [r["tool_name"] for r in result["tool_results"]]
    assert "search_knowledge" in tool_names


def test_rag_retrieval_failure_is_non_fatal():
    """
    When the retrieval service raises an exception the investigation
    must still complete. The failure must be recorded in errors and
    rag_context must remain None.
    """
    from app.ai.rag.access.policy import KnowledgeAccessContext

    access_context = KnowledgeAccessContext(user_id=1, team_id=None)

    registry = create_tool_registry(
        incident_service=FakeIncidentService(),
        deployment_service=FakeDeploymentService(),
        incident_event_service=FakeIncidentEventService(),
        knowledge_retrieval_service=FailingKnowledgeRetrievalService(),
        knowledge_access_context=access_context,
    )

    graph = InvestigationGraph(
        tool_registry=registry,
        llm_provider=FakeLLMProvider(),
    )

    state = create_initial_investigation_state(
        incident_id=1,
        user_question="Why is Payment API failing?",
    )

    result = graph.graph.invoke(state)

    assert result["status"] == "COMPLETED"
    assert result["current_stage"] == "completed"

    assert result["rag_context"] is None
    assert result["rag_citations"] == []

    rag_errors = [
        e for e in result["errors"]
        if e.get("stage") == "retrieve_knowledge"
    ]
    assert len(rag_errors) == 1
