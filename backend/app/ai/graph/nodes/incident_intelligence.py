from __future__ import annotations

import logging
from typing import Any

from app.ai.intelligence.analyzer import IncidentIntelligenceAnalyzer
from app.ai.intelligence.schemas import IncidentIntelligenceResult
from app.ai.state.investigation_state import InvestigationState

logger = logging.getLogger(__name__)


def build_incident_intelligence(
    state: InvestigationState,
    analyzer: IncidentIntelligenceAnalyzer | None = None,
) -> dict[str, Any]:
    """
    LangGraph node: generates correlated incident intelligence,
    multi-candidate root causes, impact assessment, and operational decision.
    """
    if state.get("status") == "FAILED":
        return {}

    incident_result = next(
        (
            item
            for item in state.get("tool_results", [])
            if (
                item.get("tool_name") == "get_incident"
                and item.get("status") == "SUCCESS"
            )
        ),
        None,
    )

    if incident_result is None:
        return {
            "status": "FAILED",
            "current_stage": "incident_intelligence_failed",
            "errors": [
                {
                    "stage": "incident_intelligence",
                    "error_code": "INCIDENT_DATA_UNAVAILABLE",
                    "error_message": "Successful incident retrieval result not found.",
                }
            ],
        }

    incident = incident_result.get("data", {})

    # Extract events
    events: list[dict[str, Any]] = []
    events_tool = next(
        (
            item
            for item in state.get("tool_results", [])
            if (
                item.get("tool_name") == "get_incident_events"
                and item.get("status") == "SUCCESS"
            )
        ),
        None,
    )
    if events_tool and isinstance(events_tool.get("data"), list):
        events = events_tool["data"]
    else:
        events = [
            ev
            for ev in state.get("evidence", [])
            if ev.get("source_type") in ("EVENT", "INCIDENT_EVENT")
        ]

    # Extract deployments
    deployments: list[dict[str, Any]] = []
    deployments_tool = next(
        (
            item
            for item in state.get("tool_results", [])
            if (
                item.get("tool_name") == "get_deployments"
                and item.get("status") == "SUCCESS"
            )
        ),
        None,
    )
    if deployments_tool and isinstance(deployments_tool.get("data"), list):
        deployments = deployments_tool["data"]
    else:
        deployments = [
            ev
            for ev in state.get("evidence", [])
            if ev.get("source_type") == "DEPLOYMENT"
        ]

    # Findings
    findings = state.get("findings", [])

    # Knowledge evidence
    knowledge_evidence = [
        ev
        for ev in state.get("evidence", [])
        if (ev.get("source_type") or "").upper() in ("KNOWLEDGE_BASE", "KNOWLEDGE", "RAG")
    ]

    # Risk prediction
    risk_prediction = state.get("risk_prediction")

    # Valid evidence IDs
    evidence_items = state.get("evidence", [])
    valid_evidence_ids = {
        ev.get("evidence_id")
        for ev in evidence_items
        if ev.get("evidence_id") is not None
    }

    if analyzer is None:
        analyzer = IncidentIntelligenceAnalyzer()

    try:
        intelligence = analyzer.analyze(
            incident_id=state.get("incident_id", 0),
            investigation_id=state.get("investigation_id") or 0,
            incident=incident,
            events=events,
            deployments=deployments,
            findings=findings,
            knowledge_evidence=knowledge_evidence,
            risk_prediction=risk_prediction,
            evidence_items=evidence_items,
            valid_evidence_ids=valid_evidence_ids,
        )

        return {
            "status": "COMPLETED",
            "current_stage": "completed",
            "incident_intelligence": intelligence.model_dump(mode="json"),
        }

    except Exception as exc:
        logger.exception("Failed to build incident intelligence: %s", exc)
        return {
            "status": "FAILED",
            "current_stage": "incident_intelligence_failed",
            "errors": [
                {
                    "stage": "incident_intelligence",
                    "error_code": "INTELLIGENCE_GENERATION_ERROR",
                    "error_message": str(exc),
                }
            ],
        }
