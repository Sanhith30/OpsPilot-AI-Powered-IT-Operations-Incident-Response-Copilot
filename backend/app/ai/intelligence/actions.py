from __future__ import annotations

from typing import Any

from app.ai.intelligence.schemas import CorrelatedSignal, RecommendedAction, RootCauseCandidate


class ActionRecommendationEngine:
    """
    Synthesizes operational evidence, root cause candidates, and knowledge runbooks
    into prioritized, actionable recommendations.
    CRITICAL INVARIANT: requires_human_approval MUST be True for all production-changing actions.
    """

    def recommend(
        self,
        *,
        root_causes: list[RootCauseCandidate],
        signals: list[CorrelatedSignal],
        deployments: list[dict[str, Any]] | None = None,
        knowledge_evidence: list[dict[str, Any]] | None = None,
        valid_evidence_ids: set[int] | None = None,
    ) -> list[RecommendedAction]:
        deployments = deployments or []
        knowledge_evidence = knowledge_evidence or []
        valid_evidence_ids = valid_evidence_ids or set()

        actions: list[RecommendedAction] = []
        action_count = 0

        def _next_action_id() -> str:
            nonlocal action_count
            action_count += 1
            return f"ACT-{action_count:03d}"

        # Collect evidence IDs from top root causes and signals
        top_cause = root_causes[0] if root_causes else None
        top_evidence_ids = [
            eid
            for s in signals
            for eid in s.evidence_ids
            if eid in valid_evidence_ids
        ]

        has_deployment = len(deployments) > 0 or any(s.signal_type == "DEPLOYMENT" for s in signals)
        has_pool_exhaustion = any(
            "pool" in c.cause.lower() or "connection" in c.cause.lower()
            for c in root_causes
        )

        # 1. Investigate action
        if has_pool_exhaustion:
            actions.append(
                RecommendedAction(
                    action_id=_next_action_id(),
                    title="Inspect active database connections and pool metrics",
                    description=(
                        "Query database pg_stat_activity and application connection pool utilization metrics "
                        "to determine whether pooled connections are stuck or leaking."
                    ),
                    action_type="INVESTIGATE",
                    priority="HIGH",
                    requires_human_approval=True,
                    source_evidence_ids=sorted(list(set(top_evidence_ids[:3]))),
                    rationale="High probability of connection pool exhaustion identified as primary driver of timeouts.",
                )
            )

            actions.append(
                RecommendedAction(
                    action_id=_next_action_id(),
                    title="Verify connection-pool sizing and max_connections configuration",
                    description=(
                        "Validate application pool limits against PostgreSQL max_connections setting "
                        "and compare with current worker thread count."
                    ),
                    action_type="MITIGATE",
                    priority="HIGH",
                    requires_human_approval=True,
                    source_evidence_ids=sorted(list(set(top_evidence_ids[:2]))),
                    rationale="Ensures application configuration does not exceed available backend connection limits.",
                )
            )
        else:
            actions.append(
                RecommendedAction(
                    action_id=_next_action_id(),
                    title="Inspect service logs and telemetry metrics",
                    description="Analyze error rates, latency spikes, and dependency status.",
                    action_type="INVESTIGATE",
                    priority="HIGH",
                    requires_human_approval=True,
                    source_evidence_ids=sorted(list(set(top_evidence_ids[:2]))),
                    rationale="Investigate active operational degradation telemetry.",
                )
            )

        # 2. Deployment rollback action if recent deployment exists
        if has_deployment:
            actions.append(
                RecommendedAction(
                    action_id=_next_action_id(),
                    title="Evaluate deployment rollback using approved rollback SOP",
                    description=(
                        "Compare recent release configuration changes and execute rollback to previous "
                        "known-good build artifact if connection pool regression is confirmed."
                    ),
                    action_type="ROLLBACK",
                    priority="HIGH",
                    requires_human_approval=True,
                    source_evidence_ids=sorted(list(set(top_evidence_ids[:3]))),
                    rationale="Incident onset strongly correlates with recent deployment release timestamp.",
                )
            )

        # 3. Knowledge / Runbook guidance action
        if knowledge_evidence:
            kb_ev_ids = [
                kb.get("evidence_id")
                for kb in knowledge_evidence
                if kb.get("evidence_id") in valid_evidence_ids
            ]
            actions.append(
                RecommendedAction(
                    action_id=_next_action_id(),
                    title="Apply mitigation procedures from retrieved runbook",
                    description="Follow established runbook steps to isolate downstream service impact and reset stuck pools.",
                    action_type="MITIGATE",
                    priority="MEDIUM",
                    requires_human_approval=True,
                    source_evidence_ids=[int(x) for x in kb_ev_ids if x is not None],
                    rationale="Retrieved authorized operational runbook contains standard remediation guidelines.",
                )
            )

        # 4. Verification action
        actions.append(
            RecommendedAction(
                action_id=_next_action_id(),
                title="Verify service health and readiness endpoints post-mitigation",
                description="Probe /health/ready, /health/live, and synthetic payment test transactions.",
                action_type="VERIFY",
                priority="HIGH",
                requires_human_approval=True,
                source_evidence_ids=sorted(list(set(top_evidence_ids[:2]))),
                rationale="Validates error rate normalization before closing incident.",
            )
        )

        return actions
