from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
import pytest
from pydantic import ValidationError as PydanticValidationError

from app.ai.intelligence.actions import ActionRecommendationEngine
from app.ai.intelligence.analyzer import IncidentIntelligenceAnalyzer
from app.ai.intelligence.correlation import CorrelationConfig, IncidentCorrelationEngine
from app.ai.intelligence.decision import OperationalDecisionEngine
from app.ai.intelligence.impact import ImpactAssessmentEngine
from app.ai.intelligence.root_cause import RootCauseEngine
from app.ai.intelligence.safety import IntelligenceSafetyGate
from app.ai.intelligence.schemas import (
    CorrelatedSignal,
    ImpactAssessment,
    IncidentIntelligenceResult,
    OperationalDecision,
    RecommendedAction,
    RootCauseCandidate,
)
from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.models.incident_intelligence import IncidentIntelligence
from app.repositories.incident_intelligence_repository import IncidentIntelligenceRepository
from app.services.incident_intelligence_service import IncidentIntelligenceService


# ============================================================
# 1. Schema Tests
# ============================================================

def test_correlated_signal_schema_valid():
    sig = CorrelatedSignal(
        signal_type="DEPLOYMENT",
        source_id="deployment-42",
        description="Recent release before incident",
        relevance=Decimal("0.85"),
        evidence_ids=[101, 102],
    )
    assert sig.signal_type == "DEPLOYMENT"
    assert sig.relevance == Decimal("0.85")
    assert sig.evidence_ids == [101, 102]


def test_correlated_signal_schema_invalid_relevance():
    with pytest.raises(PydanticValidationError):
        CorrelatedSignal(
            signal_type="EVENT",
            source_id="event-1",
            description="Test",
            relevance=Decimal("1.5"),  # ge=0, le=1
        )


def test_root_cause_candidate_schema():
    cand = RootCauseCandidate(
        cause="Database connection pool exhaustion",
        confidence=Decimal("0.87"),
        supporting_evidence_ids=[101],
        contradicting_evidence_ids=[],
        supporting_signals=["connection timeout"],
        contradicting_signals=[],
        explanation="Correlated timeouts and pool metrics support this cause.",
    )
    assert cand.cause == "Database connection pool exhaustion"
    assert cand.confidence == Decimal("0.87")


def test_impact_assessment_schema():
    impact = ImpactAssessment(
        severity="HIGH",
        customer_impact="Checkout requests intermittently failing",
        service_impact="Payment API availability degraded",
        operational_scope="Payment service production",
        confidence=Decimal("0.90"),
    )
    assert impact.severity == "HIGH"
    assert impact.confidence == Decimal("0.90")


def test_recommended_action_approval_default():
    action = RecommendedAction(
        action_id="ACT-001",
        title="Inspect active connections",
        description="Run pg_stat_activity",
        action_type="INVESTIGATE",
        priority="HIGH",
        source_evidence_ids=[101],
        rationale="Timeout investigation",
    )
    assert action.requires_human_approval is True


def test_operational_decision_approval_default():
    dec = OperationalDecision(
        decision="MITIGATE",
        confidence=Decimal("0.85"),
        rationale="High severity with confirmed cause",
    )
    assert dec.requires_human_approval is True


# ============================================================
# 2. Correlation Engine Tests
# ============================================================

def test_correlation_deployment_window():
    engine = IncidentCorrelationEngine(CorrelationConfig(deployment_window_minutes=30))
    incident = {
        "service": "payment-service",
        "started_at": "2026-09-28T14:30:00Z",
        "severity": "HIGH",
        "description": "504 gateway timeout and connection errors",
    }
    deployments = [
        {
            "deployment_id": 99,
            "service": "payment-service",
            "deployed_at": "2026-09-28T14:15:00Z",  # 15 min prior
        }
    ]
    evidence_items = [
        {"evidence_id": 501, "source_reference": "99", "source_type": "DEPLOYMENT"}
    ]

    signals = engine.correlate(
        incident=incident,
        deployments=deployments,
        evidence_items=evidence_items,
    )

    dep_sigs = [s for s in signals if s.signal_type == "DEPLOYMENT"]
    assert len(dep_sigs) == 1
    assert "15 min prior" in dep_sigs[0].description
    assert dep_sigs[0].evidence_ids == [501]


def test_correlation_database_connection_events():
    engine = IncidentCorrelationEngine()
    events = [
        {"event_id": 1, "summary": "database connection timeout", "details": "connect timeout after 5000ms"},
        {"event_id": 2, "summary": "connection pool exhausted", "details": "pool size 50 reached"},
    ]
    evidence_items = [
        {"evidence_id": 601, "source_reference": "1", "source_type": "EVENT"},
        {"evidence_id": 602, "source_reference": "2", "source_type": "EVENT"},
    ]

    signals = engine.correlate(
        incident={"service": "payment-api", "severity": "HIGH"},
        events=events,
        evidence_items=evidence_items,
    )

    corr_sig = next((s for s in signals if s.source_id == "correlation-db-pool-exhaustion"), None)
    assert corr_sig is not None
    assert corr_sig.relevance >= Decimal("0.90")
    assert 601 in corr_sig.evidence_ids
    assert 602 in corr_sig.evidence_ids


def test_correlation_downstream_504_database():
    engine = IncidentCorrelationEngine()
    incident = {
        "service": "payment-api",
        "severity": "HIGH",
        "description": "Payment API returning HTTP 504",
    }
    events = [
        {"event_id": 10, "summary": "database timeout", "details": "query timeout"},
    ]
    evidence_items = [
        {"evidence_id": 701, "source_reference": "10", "source_type": "EVENT"},
    ]

    signals = engine.correlate(
        incident=incident,
        events=events,
        evidence_items=evidence_items,
    )

    sig_504 = next((s for s in signals if s.source_id == "correlation-downstream-db-504"), None)
    assert sig_504 is not None
    assert 701 in sig_504.evidence_ids


def test_correlation_handles_empty_inputs():
    engine = IncidentCorrelationEngine()
    signals = engine.correlate()
    assert isinstance(signals, list)
    assert len(signals) == 0


# ============================================================
# 3. Root Cause Engine Tests
# ============================================================

def test_root_cause_multi_candidate_ordered_by_confidence():
    engine = RootCauseEngine()
    signals = [
        CorrelatedSignal(
            signal_type="EVENT",
            source_id="correlation-db-pool-exhaustion",
            description="DATABASE_CONNECTION_CORRELATION: pool exhausted",
            relevance=Decimal("0.95"),
            evidence_ids=[101],
        ),
        CorrelatedSignal(
            signal_type="DEPLOYMENT",
            source_id="deployment-1",
            description="Recent deployment detected",
            relevance=Decimal("0.85"),
            evidence_ids=[102],
        ),
        CorrelatedSignal(
            signal_type="EVENT",
            source_id="correlation-downstream-db-504",
            description="504 gateway timeout",
            relevance=Decimal("0.90"),
            evidence_ids=[103],
        ),
    ]

    valid_eids = {101, 102, 103}
    candidates = engine.generate_candidates(
        signals=signals,
        valid_evidence_ids=valid_eids,
    )

    assert len(candidates) >= 2
    # Verify strictly ordered descending by confidence
    for i in range(len(candidates) - 1):
        assert candidates[i].confidence >= candidates[i + 1].confidence

    # Verify all cited evidence IDs exist in valid_evidence_ids
    for cand in candidates:
        for eid in cand.supporting_evidence_ids:
            assert eid in valid_eids
        assert len(cand.explanation) > 0


def test_root_cause_excludes_nonexistent_evidence_ids():
    engine = RootCauseEngine()
    signals = [
        CorrelatedSignal(
            signal_type="EVENT",
            source_id="event-1",
            description="database connection timeout",
            relevance=Decimal("0.80"),
            evidence_ids=[9999],  # does not exist in valid_eids
        )
    ]
    candidates = engine.generate_candidates(
        signals=signals,
        valid_evidence_ids={101, 102},  # 9999 is absent
    )

    for cand in candidates:
        assert 9999 not in cand.supporting_evidence_ids


# ============================================================
# 4. Impact Assessment Tests
# ============================================================

def test_impact_assessment_grounded_without_hallucinations():
    engine = ImpactAssessmentEngine()
    incident = {
        "service": "payment-api",
        "severity": "HIGH",
        "description": "Payment API checkout requests are failing with 504 timeouts.",
    }
    events = [{"event_id": 1, "summary": "database timeout"}]

    impact = engine.assess(incident=incident, events=events)

    assert impact.severity == "HIGH"
    assert "checkout" in impact.customer_impact.lower()
    # Check that fabricated customer counts like '12,500' are not present
    assert "12,500" not in impact.customer_impact
    assert "users affected" not in impact.customer_impact.lower()
    assert impact.confidence >= Decimal("0.70")


# ============================================================
# 5. Action Recommendation Tests
# ============================================================

def test_action_recommendations_enforce_human_approval():
    engine = ActionRecommendationEngine()
    root_causes = [
        RootCauseCandidate(
            cause="Database connection pool exhaustion",
            confidence=Decimal("0.87"),
            supporting_evidence_ids=[101],
            explanation="Pool exhausted",
        )
    ]
    signals = [
        CorrelatedSignal(
            signal_type="DEPLOYMENT",
            source_id="deployment-1",
            description="Recent release",
            relevance=Decimal("0.85"),
            evidence_ids=[102],
        )
    ]

    actions = engine.recommend(
        root_causes=root_causes,
        signals=signals,
        deployments=[{"deployment_id": 1}],
        valid_evidence_ids={101, 102},
    )

    assert len(actions) >= 3
    action_types = [a.action_type for a in actions]
    assert "INVESTIGATE" in action_types
    assert "ROLLBACK" in action_types
    assert "VERIFY" in action_types

    for act in actions:
        assert act.requires_human_approval is True
        for eid in act.source_evidence_ids:
            assert eid in {101, 102}


# ============================================================
# 6. Operational Decision Engine Tests
# ============================================================

def test_decision_engine_high_severity_and_confident_root_cause():
    engine = OperationalDecisionEngine()
    impact = ImpactAssessment(
        severity="HIGH",
        customer_impact="Checkout failing",
        service_impact="Degraded",
        operational_scope="Production",
        confidence=Decimal("0.90"),
    )
    root_causes = [
        RootCauseCandidate(
            cause="Database connection pool exhaustion",
            confidence=Decimal("0.87"),
            explanation="Clear signals",
        )
    ]
    risk = {"level": "HIGH", "score": 0.85}

    decision = engine.decide(
        impact=impact,
        root_causes=root_causes,
        risk_assessment=risk,
    )

    assert decision.decision == "MITIGATE"
    assert decision.requires_human_approval is True
    assert decision.confidence == Decimal("0.87")


def test_decision_engine_critical_with_low_confidence_escalates():
    engine = OperationalDecisionEngine()
    impact = ImpactAssessment(
        severity="CRITICAL",
        customer_impact="Widespread outage",
        service_impact="Unavailable",
        operational_scope="Production",
        confidence=Decimal("0.95"),
    )
    root_causes = [
        RootCauseCandidate(
            cause="Unknown cascading failure",
            confidence=Decimal("0.45"),
            explanation="Ambiguous telemetry",
        )
    ]

    decision = engine.decide(
        impact=impact,
        root_causes=root_causes,
        risk_assessment={"level": "CRITICAL"},
    )

    assert decision.decision == "ESCALATE"
    assert decision.requires_human_approval is True


def test_decision_engine_low_severity_monitors():
    engine = OperationalDecisionEngine()
    impact = ImpactAssessment(
        severity="LOW",
        customer_impact="Negligible",
        service_impact="Nominal",
        operational_scope="Dev/Staging",
        confidence=Decimal("0.80"),
    )

    decision = engine.decide(
        impact=impact,
        root_causes=[],
        risk_assessment={"level": "LOW"},
    )

    assert decision.decision == "MONITOR"
    assert decision.requires_human_approval is True


# ============================================================
# 7. Safety Gate Tests
# ============================================================

def test_safety_gate_rejects_invalid_evidence_id():
    gate = IntelligenceSafetyGate()
    result = IncidentIntelligenceResult(
        incident_id=1,
        investigation_id=2,
        incident_summary="Test",
        correlated_signals=[
            CorrelatedSignal(
                signal_type="EVENT",
                source_id="event-1",
                description="Test",
                relevance=Decimal("0.80"),
                evidence_ids=[99999],  # does not exist
            )
        ],
        probable_root_causes=[],
        impact_assessment=ImpactAssessment(
            severity="MEDIUM",
            customer_impact="None",
            service_impact="None",
            operational_scope="Scope",
            confidence=Decimal("0.80"),
        ),
        operational_decision=OperationalDecision(
            decision="INVESTIGATE",
            confidence=Decimal("0.80"),
            rationale="Test",
            requires_human_approval=True,
        ),
        confidence=Decimal("0.80"),
    )

    val = gate.validate(result=result, valid_evidence_ids={101, 102})
    assert not val.is_valid
    assert "Invalid evidence IDs detected" in val.error_message


def test_safety_gate_rejects_unauthorized_evidence_id():
    gate = IntelligenceSafetyGate()
    result = IncidentIntelligenceResult(
        incident_id=1,
        investigation_id=2,
        incident_summary="Test",
        correlated_signals=[
            CorrelatedSignal(
                signal_type="KNOWLEDGE",
                source_id="kb-1",
                description="Secret runbook",
                relevance=Decimal("0.90"),
                evidence_ids=[201],
            )
        ],
        probable_root_causes=[],
        impact_assessment=ImpactAssessment(
            severity="MEDIUM",
            customer_impact="None",
            service_impact="None",
            operational_scope="Scope",
            confidence=Decimal("0.80"),
        ),
        operational_decision=OperationalDecision(
            decision="INVESTIGATE",
            confidence=Decimal("0.80"),
            rationale="Test",
            requires_human_approval=True,
        ),
        confidence=Decimal("0.80"),
    )

    # 201 exists but is not in authorized_evidence_ids
    val = gate.validate(
        result=result,
        valid_evidence_ids={201},
        authorized_evidence_ids={101},  # 201 is unauthorized
    )
    assert not val.is_valid
    assert "Unauthorized evidence IDs detected" in val.error_message


def test_safety_gate_rejects_missing_human_approval():
    gate = IntelligenceSafetyGate()
    result = IncidentIntelligenceResult(
        incident_id=1,
        investigation_id=2,
        incident_summary="Test",
        probable_root_causes=[],
        impact_assessment=ImpactAssessment(
            severity="MEDIUM",
            customer_impact="None",
            service_impact="None",
            operational_scope="Scope",
            confidence=Decimal("0.80"),
        ),
        recommended_actions=[
            RecommendedAction(
                action_id="ACT-001",
                title="Restart DB",
                description="Autonomous restart",
                action_type="MITIGATE",
                priority="HIGH",
                requires_human_approval=False,  # VIOLATION!
                rationale="Fast fix",
            )
        ],
        operational_decision=OperationalDecision(
            decision="MITIGATE",
            confidence=Decimal("0.80"),
            rationale="Test",
            requires_human_approval=True,
        ),
        confidence=Decimal("0.80"),
    )

    val = gate.validate(result=result, valid_evidence_ids=set())
    assert not val.is_valid
    assert "requires_human_approval must be True" in val.error_message


def test_safety_gate_caps_confidence_when_no_evidence():
    gate = IntelligenceSafetyGate()
    result = IncidentIntelligenceResult(
        incident_id=1,
        investigation_id=2,
        incident_summary="Test",
        probable_root_causes=[
            RootCauseCandidate(
                cause="Fabricated cause",
                confidence=Decimal("0.95"),  # Exceeds 0.60 with 0 evidence!
                explanation="No evidence backing",
            )
        ],
        impact_assessment=ImpactAssessment(
            severity="MEDIUM",
            customer_impact="None",
            service_impact="None",
            operational_scope="Scope",
            confidence=Decimal("0.80"),
        ),
        operational_decision=OperationalDecision(
            decision="INVESTIGATE",
            confidence=Decimal("0.80"),
            rationale="Test",
            requires_human_approval=True,
        ),
        confidence=Decimal("0.80"),
    )

    val = gate.validate(result=result, valid_evidence_ids=set())
    assert not val.is_valid
    assert "without any underlying operational evidence" in val.error_message


# ============================================================
# 8. Repository Persistence Tests
# ============================================================

def test_incident_intelligence_repository_lifecycle(db_session):
    repo = IncidentIntelligenceRepository(db_session)

    # Use existing incident 1 and investigation 1 from seed data
    model = IncidentIntelligence(
        incident_id=1,
        investigation_id=1,
        incident_summary="Payment API connection pool exhaustion detected",
        correlated_signals=[
            {"signal_type": "DEPLOYMENT", "source_id": "dep-1", "relevance": "0.85", "evidence_ids": []}
        ],
        probable_root_causes=[
            {"cause": "Connection pool exhaustion", "confidence": "0.87", "supporting_evidence_ids": [], "explanation": "Test"}
        ],
        impact_assessment={"severity": "HIGH", "customer_impact": "Failing requests", "service_impact": "Degraded", "operational_scope": "Prod", "confidence": "0.90"},
        risk_assessment={"score": 0.8, "level": "HIGH"},
        recommended_actions=[
            {"action_id": "ACT-001", "title": "Inspect DB", "action_type": "INVESTIGATE", "priority": "HIGH", "requires_human_approval": True, "source_evidence_ids": [], "rationale": "Investigate"}
        ],
        operational_decision={"decision": "MITIGATE", "confidence": "0.85", "rationale": "High risk", "requires_human_approval": True},
        overall_confidence=Decimal("0.8500"),
        model_name="test_model",
        model_version="1.0.0",
    )

    added = repo.add(model)
    db_session.flush()

    assert added.intelligence_id is not None

    fetched = repo.get_by_id(added.intelligence_id)
    assert fetched is not None
    assert fetched.incident_id == 1
    assert fetched.incident_summary == "Payment API connection pool exhaustion detected"
    assert fetched.overall_confidence == Decimal("0.8500")

    latest_by_inc = repo.get_latest_by_incident(1)
    assert latest_by_inc is not None
    assert latest_by_inc.intelligence_id == added.intelligence_id

    latest_by_inv = repo.get_latest_by_investigation(1)
    assert latest_by_inv is not None
    assert latest_by_inv.intelligence_id == added.intelligence_id


# ============================================================
# 9. Service Orchestration & Audit Tests
# ============================================================

def test_incident_intelligence_service_generation(db_session):
    from app.repositories.incident_repository import IncidentRepository
    from app.repositories.investigation_repository import InvestigationRepository
    from app.repositories.user_repository import UserRepository
    from app.repositories.audit_log_repository import AuditLogRepository
    from app.services.audit_log_service import AuditLogService

    intel_repo = IncidentIntelligenceRepository(db_session)
    inc_repo = IncidentRepository(db_session)
    inv_repo = InvestigationRepository(db_session)
    user_repo = UserRepository(db_session)
    audit_repo = AuditLogRepository(db_session)
    audit_svc = AuditLogService(db_session, audit_repo, user_repo)

    service = IncidentIntelligenceService(
        db=db_session,
        intelligence_repository=intel_repo,
        incident_repository=inc_repo,
        investigation_repository=inv_repo,
        audit_log_service=audit_svc,
    )

    # Run generation for existing incident 1, investigation 1
    result = service.generate(
        incident_id=1,
        investigation_id=1,
        user_id=1,
        request_id="req-test-18",
    )

    assert result.incident_id == 1
    assert result.investigation_id == 1
    assert result.operational_decision.requires_human_approval is True
    assert len(result.probable_root_causes) >= 1
    assert len(result.recommended_actions) >= 1
    for act in result.recommended_actions:
        assert act.requires_human_approval is True

    # Verify persisted in database
    latest = intel_repo.get_latest_by_incident(1)
    assert latest is not None
    assert latest.incident_id == 1

    # Verify audit log recorded
    logs = audit_svc.get_by_resource(resource_type="INCIDENT_INTELLIGENCE", resource_id=str(latest.intelligence_id))
    assert len(logs) >= 1
    assert logs[0].action == "INCIDENT_INTELLIGENCE_GENERATED"
    assert logs[0].action_result == "SUCCESS"


def test_incident_intelligence_service_fails_closed_on_safety_violation(db_session):
    from app.repositories.incident_repository import IncidentRepository
    from app.repositories.investigation_repository import InvestigationRepository
    from app.repositories.user_repository import UserRepository
    from app.repositories.audit_log_repository import AuditLogRepository
    from app.services.audit_log_service import AuditLogService

    intel_repo = IncidentIntelligenceRepository(db_session)
    inc_repo = IncidentRepository(db_session)
    inv_repo = InvestigationRepository(db_session)
    user_repo = UserRepository(db_session)
    audit_repo = AuditLogRepository(db_session)
    audit_svc = AuditLogService(db_session, audit_repo, user_repo)

    class HostileSafetyGate(IntelligenceSafetyGate):
        def validate(self, **kwargs):
            from app.ai.intelligence.safety import SafetyValidationResult
            return SafetyValidationResult(is_valid=False, violations=["Simulated safety violation"])

    service = IncidentIntelligenceService(
        db=db_session,
        intelligence_repository=intel_repo,
        incident_repository=inc_repo,
        investigation_repository=inv_repo,
        audit_log_service=audit_svc,
        safety_gate=HostileSafetyGate(),
    )

    with pytest.raises(ValidationError) as exc_info:
        service.generate(
            incident_id=1,
            investigation_id=1,
            user_id=1,
        )

    assert "safety validation" in str(exc_info.value)


# ============================================================
# 10. API Route Tests
# ============================================================

def test_api_generate_and_get_incident_intelligence(client):
    from app.core.security import create_access_token

    headers = {"Authorization": f"Bearer {create_access_token(user_id=1)}"}

    # Generate intelligence for incident 1, investigation 1
    post_resp = client.post(
        "/api/v1/incidents/1/intelligence?investigation_id=1",
        headers=headers,
    )
    assert post_resp.status_code == 200
    data = post_resp.json()
    assert data["incident_id"] == 1
    assert data["investigation_id"] == 1
    assert data["operational_decision"]["requires_human_approval"] is True
    assert len(data["recommended_actions"]) >= 1

    # Get intelligence for incident 1
    get_inc_resp = client.get(
        "/api/v1/incidents/1/intelligence",
        headers=headers,
    )
    assert get_inc_resp.status_code == 200
    assert get_inc_resp.json()["incident_id"] == 1

    # Get intelligence for investigation 1
    get_inv_resp = client.get(
        "/api/v1/investigations/1/intelligence",
        headers=headers,
    )
    assert get_inv_resp.status_code == 200
    assert get_inv_resp.json()["investigation_id"] == 1


# ============================================================
# 11. LangGraph E2E Test with Payment API Scenario
# ============================================================

def test_langgraph_e2e_payment_api_incident_intelligence():
    from app.ai.graph.investigation_graph import InvestigationGraph
    from app.ai.state.factory import create_initial_investigation_state
    from app.ai.tools.registry_factory import create_tool_registry

    class FakeIncident:
        incident_id = 1
        incident_number = "INC-1042"
        service_id = 1
        title = "Payment API elevated 504 gateway timeout and latency"
        description = "Payment API database connection timeout and pool exhaustion detected."
        severity = "HIGH"
        status = "INVESTIGATING"
        started_at = datetime(2026, 9, 28, 14, 30, tzinfo=timezone.utc)
        detected_at = datetime(2026, 9, 28, 14, 32, tzinfo=timezone.utc)
        resolved_at = None
        assigned_team_id = 1
        assigned_user_id = 2
        impact_summary = "Payment checkout failures"
        root_cause = None

    class FakeIncidentService:
        def get_incident_by_id(self, incident_id):
            return FakeIncident()

    class FakeDeployment:
        deployment_id = 101
        service_id = 1
        version = "2.9.0"
        environment = "production"
        commit_hash = "abc123"
        deployment_type = "STANDARD"
        trigger_type = "MANUAL"
        status = "SUCCESS"
        started_at = datetime(2026, 9, 28, 14, 15, tzinfo=timezone.utc)
        completed_at = datetime(2026, 9, 28, 14, 20, tzinfo=timezone.utc)
        deployed_by = 4

    class FakeDeploymentService:
        def get_recent_deployments(self, *, service_id, environment, before_time, limit):
            return [FakeDeployment()]

    class FakeIncidentEventService:
        def get_events_by_incident(self, *, incident_id, before_time=None, limit=50):
            return [
                {
                    "event_id": 501,
                    "event_type": "TIMEOUT",
                    "summary": "Database connection timeout detected",
                    "details": "Client connection timeout after 5000ms",
                },
                {
                    "event_id": 502,
                    "event_type": "RESOURCE",
                    "summary": "Connection pool exhausted",
                    "details": "Pool size 50 reached max capacity",
                },
            ]

    class FakeLLM:
        def generate(self, *, system_prompt, user_prompt, temperature=0.0, response_schema=None, **kwargs):
            return """
            {
              "summary": "Payment API connection pool exhaustion following release 2.9.0.",
              "findings": [
                {
                  "finding": "Database connection pool exhausted causing 504 errors.",
                  "confidence": "HIGH",
                  "evidence_refs": []
                }
              ],
              "probable_root_cause": "Database connection pool exhaustion",
              "recommendations": ["Inspect active database connections", "Rollback release 2.9.0"]
            }
            """

    registry = create_tool_registry(
        incident_service=FakeIncidentService(),
        deployment_service=FakeDeploymentService(),
        incident_event_service=FakeIncidentEventService(),
    )

    graph = InvestigationGraph(
        tool_registry=registry,
        llm_provider=FakeLLM(),
    )

    state = create_initial_investigation_state(
        incident_id=1,
        user_question="What is causing the Payment API 504 errors and what action should we take?",
    )

    result = graph.graph.invoke(state)

    # Assert complete end-to-end execution
    assert result["status"] == "COMPLETED"
    assert result["current_stage"] == "completed"
    assert result["risk_prediction"] is not None
    assert result["incident_intelligence"] is not None

    intel = result["incident_intelligence"]
    assert intel["incident_id"] == 1
    assert len(intel["probable_root_causes"]) >= 1

    top_cause = intel["probable_root_causes"][0]
    assert "connection" in top_cause["cause"].lower() or "pool" in top_cause["cause"].lower()
    assert Decimal(str(top_cause["confidence"])) >= Decimal("0.70")

    assert intel["impact_assessment"]["severity"] == "HIGH"
    assert intel["operational_decision"]["decision"] in ("MITIGATE", "INVESTIGATE")
    assert intel["operational_decision"]["requires_human_approval"] is True

    for action in intel["recommended_actions"]:
        assert action["requires_human_approval"] is True
