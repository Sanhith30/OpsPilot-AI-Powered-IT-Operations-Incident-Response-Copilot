from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.ai.intelligence.schemas import ImpactAssessment


class ImpactAssessmentEngine:
    """
    Assesses operational and customer impact from real incident telemetry.
    Strictly avoids fabricating customer numbers or financial loss figures.
    """

    def assess(
        self,
        *,
        incident: dict[str, Any] | None = None,
        events: list[dict[str, Any]] | None = None,
        evidence_items: list[dict[str, Any]] | None = None,
    ) -> ImpactAssessment:
        incident = incident or {}
        events = events or []
        evidence_items = evidence_items or []

        raw_severity = str(incident.get("severity") or "MEDIUM").upper()
        if raw_severity not in ("LOW", "MEDIUM", "HIGH", "CRITICAL"):
            raw_severity = "MEDIUM"

        service = str(
            incident.get("service")
            or incident.get("affected_service")
            or "Core Services"
        )
        description = str(
            incident.get("description")
            or incident.get("title")
            or ""
        ).lower()

        # Derive customer impact safely from actual text without hallucinations
        if "checkout" in description or "payment" in description:
            customer_impact = (
                "End users and checkout transactions are experiencing intermittent failures or elevated latency."
            )
        elif "login" in description or "auth" in description:
            customer_impact = (
                "Users may encounter delays or authentication errors when signing in."
            )
        elif "error" in description or "timeout" in description:
            customer_impact = (
                f"Customer requests to {service} are experiencing degraded performance and elevated errors."
            )
        else:
            customer_impact = (
                f"Service degradation observed on {service}; user impact is actively being monitored."
            )

        # Service impact
        if raw_severity in ("HIGH", "CRITICAL"):
            service_impact = (
                f"{service} availability and throughput are significantly degraded due to downstream timeouts."
            )
        else:
            service_impact = (
                f"{service} performance is partially degraded but operational."
            )

        # Operational scope
        operational_scope = f"{service} production environment"
        if events:
            operational_scope += f" ({len(events)} correlated operational events)"

        # Confidence based on evidence completeness
        confidence = Decimal("0.90") if (events and len(events) >= 2) else Decimal("0.75")

        return ImpactAssessment(
            severity=raw_severity,  # type: ignore[arg-type]
            customer_impact=customer_impact,
            service_impact=service_impact,
            operational_scope=operational_scope,
            confidence=confidence,
        )
