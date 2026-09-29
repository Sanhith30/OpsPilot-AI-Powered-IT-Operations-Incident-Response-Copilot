from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.ai.intelligence.schemas import (
    CorrelatedSignal,
    ImpactAssessment,
    OperationalDecision,
    RootCauseCandidate,
)


class OperationalDecisionEngine:
    """
    Synthesizes impact, risk, root causes, and correlations to reach an operational decision.
    CRITICAL INVARIANT: requires_human_approval is strictly enforced as True.
    """

    def decide(
        self,
        *,
        impact: ImpactAssessment,
        root_causes: list[RootCauseCandidate],
        risk_assessment: dict[str, Any] | None = None,
        signals: list[CorrelatedSignal] | None = None,
        incident_status: str | None = None,
    ) -> OperationalDecision:
        risk_assessment = risk_assessment or {}
        signals = signals or []

        risk_level = str(risk_assessment.get("level") or risk_assessment.get("risk_level") or "MEDIUM").upper()
        severity = impact.severity.upper()

        top_cause = root_causes[0] if root_causes else None
        top_confidence = top_cause.confidence if top_cause else Decimal("0.0")

        has_deployment = any(s.signal_type == "DEPLOYMENT" for s in signals)

        if incident_status and incident_status.upper() in ("RESOLVED", "CLOSED"):
            return OperationalDecision(
                decision="RESOLVE_PENDING_CONFIRMATION",
                confidence=Decimal("0.90"),
                rationale="Incident is marked resolved in telemetry; awaiting operator confirmation and validation.",
                requires_human_approval=True,
            )

        # High/Critical severity + high risk + high root cause confidence -> MITIGATE
        if (severity in ("HIGH", "CRITICAL") or risk_level in ("HIGH", "CRITICAL")) and top_confidence >= Decimal("0.70"):
            rationale_parts = [
                f"High operational severity ({severity}) and {risk_level} risk coupled with high root-cause confidence ({top_confidence:.2f}).",
                f"Primary suspected cause: {top_cause.cause if top_cause else 'Identified issue'}.",
            ]
            if has_deployment:
                rationale_parts.append("Correlated deployment suggests immediate rollback or configuration adjustment is viable.")
            rationale_parts.append("Recommendation: Proceed with targeted mitigation subject to human review.")

            return OperationalDecision(
                decision="MITIGATE",
                confidence=top_confidence,
                rationale=" ".join(rationale_parts),
                requires_human_approval=True,
            )

        # Critical severity but low confidence in root cause -> ESCALATE
        if severity == "CRITICAL" and top_confidence < Decimal("0.60"):
            return OperationalDecision(
                decision="ESCALATE",
                confidence=Decimal("0.85"),
                rationale="Critical severity with ambiguous root-cause signals requires immediate senior engineering escalation.",
                requires_human_approval=True,
            )

        # Low severity and low risk -> MONITOR
        if severity == "LOW" and risk_level == "LOW":
            return OperationalDecision(
                decision="MONITOR",
                confidence=Decimal("0.80"),
                rationale="Low severity operational fluctuation with minimal customer impact; continue automated monitoring.",
                requires_human_approval=True,
            )

        # Default to INVESTIGATE
        return OperationalDecision(
            decision="INVESTIGATE",
            confidence=Decimal("0.78"),
            rationale=(
                f"Incident exhibits {severity} severity with moderate risk ({risk_level}). "
                "Further log analysis and telemetry gathering recommended before active mitigation."
            ),
            requires_human_approval=True,
        )
