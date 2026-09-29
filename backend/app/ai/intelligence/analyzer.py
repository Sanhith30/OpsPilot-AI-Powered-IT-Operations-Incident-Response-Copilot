from __future__ import annotations

import json
import logging
from decimal import Decimal
from typing import Any

from pydantic import ValidationError

from app.ai.intelligence.actions import ActionRecommendationEngine
from app.ai.intelligence.correlation import IncidentCorrelationEngine
from app.ai.intelligence.decision import OperationalDecisionEngine
from app.ai.intelligence.impact import ImpactAssessmentEngine
from app.ai.intelligence.root_cause import RootCauseEngine
from app.ai.intelligence.schemas import (
    CorrelatedSignal,
    ImpactAssessment,
    IncidentIntelligenceResult,
    OperationalDecision,
    RecommendedAction,
    RootCauseCandidate,
)
from app.ai.providers.base import LLMProvider
from app.core.sanitizer import sanitize_operational_input

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the OpsPilot Incident Intelligence Analyzer.

Your job is to reason only from supplied operational evidence.

Rules:
1. Never invent evidence.
2. Never invent timestamps.
3. Never invent deployments.
4. Never invent remediation commands.
5. Every factual claim must be supported by supplied evidence.
6. Distinguish observed facts from hypotheses.
7. Return structured output only.
8. Production-changing actions must require human approval.
"""


class IncidentIntelligenceAnalyzer:
    """
    Synthesizes operational intelligence using the configured LLM provider
    with fallback to grounded deterministic intelligence engines.
    """

    def __init__(
        self,
        llm_provider: LLMProvider | None = None,
        correlation_engine: IncidentCorrelationEngine | None = None,
        root_cause_engine: RootCauseEngine | None = None,
        impact_engine: ImpactAssessmentEngine | None = None,
        action_engine: ActionRecommendationEngine | None = None,
        decision_engine: OperationalDecisionEngine | None = None,
    ) -> None:
        self.llm_provider = llm_provider
        self.correlation_engine = correlation_engine or IncidentCorrelationEngine()
        self.root_cause_engine = root_cause_engine or RootCauseEngine()
        self.impact_engine = impact_engine or ImpactAssessmentEngine()
        self.action_engine = action_engine or ActionRecommendationEngine()
        self.decision_engine = decision_engine or OperationalDecisionEngine()

    def build_user_prompt(
        self,
        *,
        incident: dict[str, Any],
        events: list[dict[str, Any]],
        deployments: list[dict[str, Any]],
        findings: list[dict[str, Any]],
        knowledge_evidence: list[dict[str, Any]],
        risk_prediction: dict[str, Any] | None,
        deterministic_correlations: list[CorrelatedSignal],
    ) -> str:
        prompt_parts = [
            "<incident>",
            sanitize_operational_input(json.dumps(incident, default=str)),
            "</incident>\n",
            "<events>",
            sanitize_operational_input(json.dumps(events, default=str)),
            "</events>\n",
            "<deployments>",
            sanitize_operational_input(json.dumps(deployments, default=str)),
            "</deployments>\n",
            "<findings>",
            sanitize_operational_input(json.dumps(findings, default=str)),
            "</findings>\n",
            "<knowledge_evidence>",
            sanitize_operational_input(json.dumps(knowledge_evidence, default=str)),
            "</knowledge_evidence>\n",
            "<risk_prediction>",
            sanitize_operational_input(json.dumps(risk_prediction or {}, default=str)),
            "</risk_prediction>\n",
            "<deterministic_correlations>",
            sanitize_operational_input(json.dumps([s.model_dump(mode="json") for s in deterministic_correlations], default=str)),
            "</deterministic_correlations>\n",
            "Synthesize this operational evidence into an IncidentIntelligenceResult. "
            "Ensure every recommended action has requires_human_approval=True.",
        ]
        return "\n".join(prompt_parts)

    def analyze(
        self,
        *,
        incident_id: int,
        investigation_id: int,
        incident: dict[str, Any],
        events: list[dict[str, Any]],
        deployments: list[dict[str, Any]],
        findings: list[dict[str, Any]],
        knowledge_evidence: list[dict[str, Any]],
        risk_prediction: dict[str, Any] | None,
        evidence_items: list[dict[str, Any]],
        valid_evidence_ids: set[int],
    ) -> IncidentIntelligenceResult:
        # 1. Deterministic correlations
        signals = self.correlation_engine.correlate(
            incident=incident,
            events=events,
            deployments=deployments,
            findings=findings,
            risk_prediction=risk_prediction,
            knowledge_evidence=knowledge_evidence,
            evidence_items=evidence_items,
        )

        # 2. Deterministic root-cause candidates
        root_causes = self.root_cause_engine.generate_candidates(
            signals=signals,
            findings=findings,
            events=events,
            deployments=deployments,
            knowledge_evidence=knowledge_evidence,
            valid_evidence_ids=valid_evidence_ids,
        )

        # 3. Deterministic impact assessment
        impact = self.impact_engine.assess(
            incident=incident,
            events=events,
            evidence_items=evidence_items,
        )

        # 4. Action recommendations
        actions = self.action_engine.recommend(
            root_causes=root_causes,
            signals=signals,
            deployments=deployments,
            knowledge_evidence=knowledge_evidence,
            valid_evidence_ids=valid_evidence_ids,
        )

        # 5. Operational decision
        decision = self.decision_engine.decide(
            impact=impact,
            root_causes=root_causes,
            risk_assessment=risk_prediction,
            signals=signals,
            incident_status=str(incident.get("status") or ""),
        )

        # Base deterministic result
        summary = (
            f"{incident.get('service', 'Service')} is experiencing {incident.get('severity', 'elevated')} severity degradation. "
            f"Primary candidate: {root_causes[0].cause if root_causes else 'Under investigation'}."
        )

        base_result = IncidentIntelligenceResult(
            incident_id=incident_id,
            investigation_id=investigation_id,
            incident_summary=summary,
            correlated_signals=signals,
            probable_root_causes=root_causes,
            impact_assessment=impact,
            risk_assessment=risk_prediction or {},
            recommended_actions=actions,
            operational_decision=decision,
            confidence=decision.confidence,
            model_name="deterministic_rules_engine",
            model_version="1.0.0",
        )

        # 6. If LLM provider is available, attempt synthesis with structured output
        if self.llm_provider is not None:
            user_prompt = self.build_user_prompt(
                incident=incident,
                events=events,
                deployments=deployments,
                findings=findings,
                knowledge_evidence=knowledge_evidence,
                risk_prediction=risk_prediction,
                deterministic_correlations=signals,
            )
            try:
                raw_response = self.llm_provider.generate(
                    system_prompt=SYSTEM_PROMPT,
                    user_prompt=user_prompt,
                    temperature=0.0,
                    response_schema=IncidentIntelligenceResult,
                )
                parsed_json = json.loads(raw_response)
                llm_result = IncidentIntelligenceResult.model_validate(parsed_json)
                
                # Enforce invariant: requires_human_approval must be True on all actions & decision
                for a in llm_result.recommended_actions:
                    a.requires_human_approval = True
                llm_result.operational_decision.requires_human_approval = True

                # Grounding guard: prune any hallucinated evidence IDs
                for s in llm_result.correlated_signals:
                    s.evidence_ids = [eid for eid in s.evidence_ids if eid in valid_evidence_ids]
                for c in llm_result.probable_root_causes:
                    c.supporting_evidence_ids = [eid for eid in c.supporting_evidence_ids if eid in valid_evidence_ids]
                    c.contradicting_evidence_ids = [eid for eid in c.contradicting_evidence_ids if eid in valid_evidence_ids]
                for a in llm_result.recommended_actions:
                    a.source_evidence_ids = [eid for eid in a.source_evidence_ids if eid in valid_evidence_ids]

                llm_result.incident_id = incident_id
                llm_result.investigation_id = investigation_id
                llm_result.model_name = getattr(self.llm_provider, "model_name", "gemini-3.8-flash")
                llm_result.model_version = "1.0.0"

                return llm_result

            except Exception as exc:
                logger.warning(
                    "LLM synthesis failed or returned unparseable output; falling back to deterministic baseline: %s",
                    exc,
                )

        return base_result
