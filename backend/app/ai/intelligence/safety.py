from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from app.ai.intelligence.schemas import IncidentIntelligenceResult


@dataclass
class SafetyValidationResult:
    is_valid: bool
    violations: list[str] = field(default_factory=list)

    @property
    def error_message(self) -> str:
        return "; ".join(self.violations)


class IntelligenceSafetyGate:
    """
    Fail-closed safety validator for Incident Intelligence.
    Enforces strict grounding, authorization, and human-in-the-loop approval.
    """

    def validate(
        self,
        *,
        result: IncidentIntelligenceResult,
        valid_evidence_ids: set[int],
        authorized_evidence_ids: set[int] | None = None,
        has_incident: bool = True,
        has_investigation: bool = True,
    ) -> SafetyValidationResult:
        violations: list[str] = []

        # 1. Missing incident or investigation
        if not has_incident or result.incident_id <= 0:
            violations.append("Missing or invalid incident: incident_id must be valid.")

        if not has_investigation or result.investigation_id <= 0:
            violations.append("Missing or invalid investigation: investigation_id must be valid.")

        # 2. Strict evidence identity check (Fail-closed against hallucinated evidence IDs)
        all_cited_eids: set[int] = set()

        for s in result.correlated_signals:
            for eid in s.evidence_ids:
                all_cited_eids.add(eid)

        for c in result.probable_root_causes:
            for eid in c.supporting_evidence_ids:
                all_cited_eids.add(eid)
            for eid in c.contradicting_evidence_ids:
                all_cited_eids.add(eid)

        for a in result.recommended_actions:
            for eid in a.source_evidence_ids:
                all_cited_eids.add(eid)

        invalid_eids = all_cited_eids - valid_evidence_ids
        if invalid_eids:
            violations.append(
                f"Invalid evidence IDs detected: {sorted(list(invalid_eids))}. "
                "Citing non-existent evidence is strictly forbidden."
            )

        # 3. Authorization check on evidence
        if authorized_evidence_ids is not None:
            unauthorized_eids = all_cited_eids - authorized_evidence_ids
            if unauthorized_eids:
                violations.append(
                    f"Unauthorized evidence IDs detected: {sorted(list(unauthorized_eids))}. "
                    "Evidence access denied by authorization policy."
                )

        # 4. Mandatory Human Approval invariant
        for act in result.recommended_actions:
            if not act.requires_human_approval:
                violations.append(
                    f"Action '{act.action_id}' violates safety policy: "
                    "requires_human_approval must be True."
                )

        if not result.operational_decision.requires_human_approval:
            violations.append(
                "Operational decision violates safety policy: "
                "requires_human_approval must be True."
            )

        # 5. No evidence -> No confident root cause rule
        if len(valid_evidence_ids) == 0:
            for c in result.probable_root_causes:
                if c.confidence > Decimal("0.60"):
                    violations.append(
                        f"Root cause candidate '{c.cause}' has confidence {c.confidence} "
                        "without any underlying operational evidence. Max confidence is 0.60."
                    )

        return SafetyValidationResult(
            is_valid=len(violations) == 0,
            violations=violations,
        )
