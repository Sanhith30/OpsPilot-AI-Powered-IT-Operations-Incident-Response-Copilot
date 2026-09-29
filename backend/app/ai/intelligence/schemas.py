from __future__ import annotations

from decimal import Decimal
from typing import Any, Literal
from pydantic import BaseModel, Field


class CorrelatedSignal(BaseModel):
    signal_type: Literal[
        "INCIDENT",
        "EVENT",
        "DEPLOYMENT",
        "KNOWLEDGE",
        "FINDING",
        "RISK",
    ]
    source_id: str
    description: str
    relevance: Decimal = Field(ge=0, le=1)
    evidence_ids: list[int] = Field(default_factory=list)


class RootCauseCandidate(BaseModel):
    cause: str
    confidence: Decimal = Field(ge=0, le=1)
    supporting_evidence_ids: list[int] = Field(default_factory=list)
    contradicting_evidence_ids: list[int] = Field(default_factory=list)
    supporting_signals: list[str] = Field(default_factory=list)
    contradicting_signals: list[str] = Field(default_factory=list)
    explanation: str


class ImpactAssessment(BaseModel):
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    customer_impact: str
    service_impact: str
    operational_scope: str
    confidence: Decimal = Field(ge=0, le=1)


class RecommendedAction(BaseModel):
    action_id: str
    title: str
    description: str
    action_type: Literal[
        "INVESTIGATE",
        "MITIGATE",
        "ESCALATE",
        "MONITOR",
        "ROLLBACK",
        "VERIFY",
    ]
    priority: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    requires_human_approval: bool = True
    source_evidence_ids: list[int] = Field(default_factory=list)
    rationale: str


class OperationalDecision(BaseModel):
    decision: Literal[
        "INVESTIGATE",
        "MITIGATE",
        "ESCALATE",
        "MONITOR",
        "RESOLVE_PENDING_CONFIRMATION",
    ]
    confidence: Decimal = Field(ge=0, le=1)
    rationale: str
    requires_human_approval: bool = True


class IncidentIntelligenceResult(BaseModel):
    incident_id: int
    investigation_id: int
    incident_summary: str
    correlated_signals: list[CorrelatedSignal] = Field(default_factory=list)
    probable_root_causes: list[RootCauseCandidate] = Field(default_factory=list)
    impact_assessment: ImpactAssessment
    risk_assessment: dict[str, Any] = Field(default_factory=dict)
    recommended_actions: list[RecommendedAction] = Field(default_factory=list)
    operational_decision: OperationalDecision
    confidence: Decimal = Field(ge=0, le=1)
    model_name: str | None = None
    model_version: str | None = None
