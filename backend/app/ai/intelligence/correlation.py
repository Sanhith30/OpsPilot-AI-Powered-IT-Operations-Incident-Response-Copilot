from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from app.ai.intelligence.schemas import CorrelatedSignal


@dataclass(frozen=True)
class CorrelationConfig:
    deployment_window_minutes: int = 30
    event_window_minutes: int = 30
    min_signal_relevance: Decimal = Decimal("0.50")


def _parse_datetime(val: Any) -> datetime | None:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val if val.tzinfo is not None else val.replace(tzinfo=timezone.utc)
    if isinstance(val, str):
        try:
            # Handle ISO format or common DB format
            dt = datetime.fromisoformat(val.replace("Z", "+00:00"))
            return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)
        except Exception:
            return None
    return None


class IncidentCorrelationEngine:
    """
    Deterministic correlation engine.
    Analyzes operational events, deployments, findings, risk predictions,
    and retrieved knowledge to produce CorrelatedSignals.
    """

    def __init__(self, config: CorrelationConfig | None = None) -> None:
        self.config = config or CorrelationConfig()

    def correlate(
        self,
        *,
        incident: dict[str, Any] | None = None,
        events: list[dict[str, Any]] | None = None,
        deployments: list[dict[str, Any]] | None = None,
        findings: list[dict[str, Any]] | None = None,
        risk_prediction: dict[str, Any] | None = None,
        knowledge_evidence: list[dict[str, Any]] | None = None,
        evidence_items: list[dict[str, Any]] | None = None,
    ) -> list[CorrelatedSignal]:
        incident = incident or {}
        events = events or []
        deployments = deployments or []
        findings = findings or []
        knowledge_evidence = knowledge_evidence or []
        evidence_items = evidence_items or []

        # Build lookup from source_id / source_reference to evidence_id
        source_to_evidence_id: dict[str, list[int]] = {}
        for ev in evidence_items:
            ev_id = ev.get("evidence_id")
            if ev_id is not None:
                src_ref = str(ev.get("source_reference") or "")
                if src_ref:
                    source_to_evidence_id.setdefault(src_ref, []).append(ev_id)
                src_name = str(ev.get("source_name") or ev.get("source") or "")
                if src_name:
                    source_to_evidence_id.setdefault(src_name, []).append(ev_id)

        signals: list[CorrelatedSignal] = []

        incident_time = _parse_datetime(
            incident.get("started_at")
            or incident.get("created_at")
            or incident.get("incident_timestamp")
        )
        incident_service = str(incident.get("service") or incident.get("affected_service") or "").lower()
        incident_severity = str(incident.get("severity") or "").upper()
        incident_description = str(incident.get("description") or incident.get("title") or "").lower()

        # ----------------------------------------------------
        # 1. DEPLOYMENT_CORRELATION
        # Recent deployment before incident
        # ----------------------------------------------------
        for dep in deployments:
            dep_id = str(dep.get("deployment_id") or dep.get("id") or "deployment")
            dep_service = str(dep.get("service") or dep.get("service_name") or "").lower()
            dep_time = _parse_datetime(
                dep.get("deployed_at")
                or dep.get("created_at")
                or dep.get("timestamp")
            )

            is_time_correlated = False
            time_diff_min = None
            if incident_time and dep_time:
                diff_seconds = (incident_time - dep_time).total_seconds()
                # If deployment occurred within window before incident (or up to 10 min after)
                if -600 <= diff_seconds <= (self.config.deployment_window_minutes * 60):
                    is_time_correlated = True
                    time_diff_min = round(diff_seconds / 60)

            # Service match
            service_match = bool(dep_service and incident_service and (dep_service in incident_service or incident_service in dep_service))

            if is_time_correlated or (dep and len(deployments) == 1):
                ev_ids = source_to_evidence_id.get(dep_id, [])
                rel = Decimal("0.85") if (is_time_correlated and service_match) else Decimal("0.75")
                desc = (
                    f"Recent deployment detected {time_diff_min} min prior to incident escalation."
                    if time_diff_min is not None
                    else "Recent service deployment correlates with incident onset."
                )
                signals.append(
                    CorrelatedSignal(
                        signal_type="DEPLOYMENT",
                        source_id=f"deployment-{dep_id}",
                        description=desc,
                        relevance=rel,
                        evidence_ids=ev_ids,
                    )
                )

        # ----------------------------------------------------
        # 2. EVENT CORRELATIONS
        # Check connection timeouts, pool exhaustion, HTTP 504
        # ----------------------------------------------------
        has_conn_timeout = False
        has_pool_exhausted = False
        has_http_504 = False
        has_db_timeout = False

        event_signals_map: dict[str, list[int]] = {}

        for ev in events:
            ev_id = str(ev.get("event_id") or ev.get("id") or "")
            ev_type = str(ev.get("event_type") or "").upper()
            ev_text = f"{ev.get('summary', '')} {ev.get('message', '')} {ev.get('details', '')}".lower()

            linked_ev_ids = source_to_evidence_id.get(ev_id, [])

            if "connection timeout" in ev_text or "connect timeout" in ev_text:
                has_conn_timeout = True
                event_signals_map.setdefault("conn_timeout", []).extend(linked_ev_ids)
            if "pool exhausted" in ev_text or "pool exhaustion" in ev_text or "connection pool" in ev_text:
                has_pool_exhausted = True
                event_signals_map.setdefault("pool_exhausted", []).extend(linked_ev_ids)
            if "504" in ev_text or "gateway timeout" in ev_text or "504" in incident_description:
                has_http_504 = True
                event_signals_map.setdefault("http_504", []).extend(linked_ev_ids)
            if "database timeout" in ev_text or "db timeout" in ev_text or "database query timeout" in ev_text:
                has_db_timeout = True
                event_signals_map.setdefault("db_timeout", []).extend(linked_ev_ids)

            # Add operational event signal
            signals.append(
                CorrelatedSignal(
                    signal_type="EVENT",
                    source_id=f"event-{ev_id}" if ev_id else f"event-{len(signals)+1}",
                    description=str(ev.get("summary") or ev.get("message") or "Operational event observed"),
                    relevance=Decimal("0.80"),
                    evidence_ids=linked_ev_ids,
                )
            )

        # Database connection correlation (timeout + pool exhaustion)
        if has_conn_timeout and has_pool_exhausted:
            combined_ev_ids = list(set(event_signals_map.get("conn_timeout", []) + event_signals_map.get("pool_exhausted", [])))
            signals.append(
                CorrelatedSignal(
                    signal_type="EVENT",
                    source_id="correlation-db-pool-exhaustion",
                    description="DATABASE_CONNECTION_CORRELATION: Connection timeout coincided with connection pool exhaustion.",
                    relevance=Decimal("0.95"),
                    evidence_ids=combined_ev_ids,
                )
            )

        # Downstream database correlation (HTTP 504 + DB timeout/conn timeout)
        if (has_http_504 or "504" in incident_description) and (has_db_timeout or has_conn_timeout or has_pool_exhausted):
            combined_ev_ids = list(set(event_signals_map.get("http_504", []) + event_signals_map.get("db_timeout", []) + event_signals_map.get("conn_timeout", [])))
            signals.append(
                CorrelatedSignal(
                    signal_type="EVENT",
                    source_id="correlation-downstream-db-504",
                    description="DOWNSTREAM_DATABASE_CORRELATION: Elevated HTTP 504 gateway responses linked to downstream database timeouts.",
                    relevance=Decimal("0.92"),
                    evidence_ids=combined_ev_ids,
                )
            )

        # ----------------------------------------------------
        # 3. ELEVATED_INCIDENT_RISK_CORRELATION
        # High severity + high error rate / deployments
        # ----------------------------------------------------
        error_rate_high = "high error rate" in incident_description or "error rate" in incident_description or incident_severity in ("HIGH", "CRITICAL")
        has_deployments = len(deployments) > 0

        if incident_severity in ("HIGH", "CRITICAL") and (error_rate_high or has_deployments):
            risk_ev_ids: list[int] = []
            for ev_list in source_to_evidence_id.values():
                risk_ev_ids.extend(ev_list)
            signals.append(
                CorrelatedSignal(
                    signal_type="RISK",
                    source_id="correlation-elevated-risk",
                    description="ELEVATED_INCIDENT_RISK_CORRELATION: High severity incident coupled with active regression signals and recent deployment.",
                    relevance=Decimal("0.90"),
                    evidence_ids=list(set(risk_ev_ids))[:5],
                )
            )

        # ----------------------------------------------------
        # 4. KNOWLEDGE BASE CORRELATION
        # ----------------------------------------------------
        for kb in knowledge_evidence:
            doc_title = kb.get("source_name") or kb.get("source") or kb.get("title") or "Knowledge Document"
            doc_id = str(kb.get("source_reference") or kb.get("document_id") or "kb")
            ev_id = kb.get("evidence_id")
            signals.append(
                CorrelatedSignal(
                    signal_type="KNOWLEDGE",
                    source_id=f"knowledge-{doc_id}",
                    description=f"Retrieved runbook/knowledge: {doc_title}",
                    relevance=Decimal("0.85"),
                    evidence_ids=[ev_id] if ev_id is not None else [],
                )
            )

        # ----------------------------------------------------
        # 5. FINDINGS CORRELATION
        # ----------------------------------------------------
        for idx, finding in enumerate(findings):
            finding_text = finding.get("finding_text") or finding.get("finding") or finding.get("title") or "Investigation finding"
            finding_id = str(finding.get("finding_id") or idx + 1)
            linked_ids = finding.get("evidence_ids") or []
            signals.append(
                CorrelatedSignal(
                    signal_type="FINDING",
                    source_id=f"finding-{finding_id}",
                    description=f"Investigation finding: {finding_text[:120]}",
                    relevance=Decimal("0.80"),
                    evidence_ids=linked_ids,
                )
            )

        # Filter by min_signal_relevance
        filtered_signals = [
            s for s in signals if s.relevance >= self.config.min_signal_relevance
        ]

        return filtered_signals
