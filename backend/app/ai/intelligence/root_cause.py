from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.ai.intelligence.schemas import CorrelatedSignal, RootCauseCandidate


class RootCauseEngine:
    """
    Root-Cause analysis engine.
    Synthesizes deterministic correlations, operational findings,
    RAG evidence, and events to generate multiple candidate causes.
    Guarantees evidence IDs cited actually exist in the investigation.
    """

    def generate_candidates(
        self,
        *,
        signals: list[CorrelatedSignal],
        findings: list[dict[str, Any]] | None = None,
        events: list[dict[str, Any]] | None = None,
        deployments: list[dict[str, Any]] | None = None,
        knowledge_evidence: list[dict[str, Any]] | None = None,
        valid_evidence_ids: set[int] | None = None,
    ) -> list[RootCauseCandidate]:
        findings = findings or []
        events = events or []
        deployments = deployments or []
        knowledge_evidence = knowledge_evidence or []
        valid_evidence_ids = valid_evidence_ids or set()

        # Collect signal descriptions and types
        signal_descs = [s.description.lower() for s in signals]
        has_deployment_sig = any(s.signal_type == "DEPLOYMENT" for s in signals)
        has_db_pool_sig = any(
            "pool exhaustion" in d or "connection pool" in d or "pool" in d
            for d in signal_descs
        )
        has_timeout_sig = any("timeout" in d for d in signal_descs)
        has_504_sig = any("504" in d or "gateway" in d for d in signal_descs)

        # Collect evidence IDs associated with specific signals
        deployment_ev_ids = [
            eid
            for s in signals
            if s.signal_type == "DEPLOYMENT"
            for eid in s.evidence_ids
            if eid in valid_evidence_ids
        ]
        db_ev_ids = [
            eid
            for s in signals
            if "database" in s.description.lower()
            or "pool" in s.description.lower()
            or "timeout" in s.description.lower()
            for eid in s.evidence_ids
            if eid in valid_evidence_ids
        ]
        kb_ev_ids = [
            eid
            for s in signals
            if s.signal_type == "KNOWLEDGE"
            for eid in s.evidence_ids
            if eid in valid_evidence_ids
        ]
        general_ev_ids = [
            eid
            for s in signals
            for eid in s.evidence_ids
            if eid in valid_evidence_ids
        ]

        candidates: list[RootCauseCandidate] = []

        # ----------------------------------------------------
        # Candidate 1: Database Connection Pool Exhaustion
        # ----------------------------------------------------
        if has_db_pool_sig or has_timeout_sig:
            supporting_sigs: list[str] = []
            if has_timeout_sig:
                supporting_sigs.append("Connection timeout events observed")
            if has_db_pool_sig:
                supporting_sigs.append("Connection pool exhaustion signal detected")
            if has_deployment_sig:
                supporting_sigs.append("Recent deployment precedes database saturation")
            if kb_ev_ids:
                supporting_sigs.append("Retrieved operational runbook matches database connection failure symptoms")

            cand_ev_ids = sorted(list(set(db_ev_ids + kb_ev_ids)))
            conf = Decimal("0.87") if (has_db_pool_sig and has_deployment_sig) else Decimal("0.72")

            explanation_parts = [
                "Multiple operational signals support database connection pool exhaustion.",
                f"Observed {len(events)} events and {len(deployments)} deployments.",
            ]
            if supporting_sigs:
                explanation_parts.append("Supporting indicators: " + "; ".join(supporting_sigs) + ".")

            candidates.append(
                RootCauseCandidate(
                    cause="Database connection pool exhaustion",
                    confidence=conf,
                    supporting_evidence_ids=cand_ev_ids,
                    contradicting_evidence_ids=[],
                    supporting_signals=supporting_sigs,
                    contradicting_signals=[],
                    explanation=" ".join(explanation_parts),
                )
            )

        # ----------------------------------------------------
        # Candidate 2: Deployment Regression / Configuration Drift
        # ----------------------------------------------------
        if has_deployment_sig:
            supporting_sigs = ["Deployment occurred shortly prior to incident escalation"]
            if has_timeout_sig or has_504_sig:
                supporting_sigs.append("Post-deployment latency and error spike")

            cand_ev_ids = sorted(list(set(deployment_ev_ids + kb_ev_ids)))
            conf = Decimal("0.68") if has_deployment_sig else Decimal("0.40")

            candidates.append(
                RootCauseCandidate(
                    cause="Deployment regression or connection configuration mismatch",
                    confidence=conf,
                    supporting_evidence_ids=cand_ev_ids,
                    contradicting_evidence_ids=[],
                    supporting_signals=supporting_sigs,
                    contradicting_signals=[],
                    explanation=(
                        "Recent deployment correlated with incident onset suggests configuration drift "
                        "or unoptimized connection pooling introduced in latest release."
                    ),
                )
            )

        # ----------------------------------------------------
        # Candidate 3: Downstream Gateway / Latency Saturation
        # ----------------------------------------------------
        if has_504_sig or has_timeout_sig:
            supporting_sigs = ["HTTP 504 Gateway Timeout responses detected"]
            cand_ev_ids = sorted(list(set(db_ev_ids[:2] + general_ev_ids[:2])))
            conf = Decimal("0.54")

            candidates.append(
                RootCauseCandidate(
                    cause="Downstream dependency latency saturation",
                    confidence=conf,
                    supporting_evidence_ids=cand_ev_ids,
                    contradicting_evidence_ids=[],
                    supporting_signals=supporting_sigs,
                    contradicting_signals=[],
                    explanation=(
                        "Intermittent gateway timeouts point to downstream service or database response "
                        "degradation affecting edge availability."
                    ),
                )
            )

        # Fallback if no specific candidate matched
        if not candidates:
            cand_ev_ids = sorted(list(set(general_ev_ids[:3])))
            candidates.append(
                RootCauseCandidate(
                    cause="Service degradation under investigation",
                    confidence=Decimal("0.50"),
                    supporting_evidence_ids=cand_ev_ids,
                    contradicting_evidence_ids=[],
                    supporting_signals=["Anomalous operational signals under review"],
                    contradicting_signals=[],
                    explanation="Preliminary investigation indicates service degradation; gathering further telemetry.",
                )
            )

        # Sort strictly by confidence descending
        candidates.sort(key=lambda c: c.confidence, reverse=True)
        return candidates
