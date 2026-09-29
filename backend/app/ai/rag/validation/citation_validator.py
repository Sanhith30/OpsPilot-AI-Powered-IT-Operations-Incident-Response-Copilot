from typing import Any

from app.ai.rag.validation.schemas import (
    CitationValidationResult,
    FindingValidationResult,
    GroundingValidationResult,
)


class CitationValidator:
    """
    Deterministic validator for RAG knowledge-base citations and grounding.
    Enforces that every KNOWLEDGE_BASE citation referenced by an AI finding
    was actually retrieved in the investigation's RAG context.
    """

    def validate_citation(
        self,
        citation_id: str,
        rag_citations: list[Any],
    ) -> CitationValidationResult:
        allowed_ids = self._extract_allowed_ids(rag_citations)
        target = str(citation_id).strip()
        is_valid = bool(target and target in allowed_ids)
        reason = (
            "Citation is valid and grounded in retrieved knowledge"
            if is_valid
            else f"Citation '{citation_id}' was not retrieved in knowledge context"
        )
        return CitationValidationResult(
            valid=is_valid,
            citation_id=citation_id,
            reason=reason,
        )

    def validate(
        self,
        findings: list[Any],
        rag_citations: list[Any],
    ) -> GroundingValidationResult:
        allowed_ids = self._extract_allowed_ids(rag_citations)
        has_rag_context = bool(rag_citations)

        findings_results: list[FindingValidationResult] = []
        all_invalid_citations: list[str] = []
        all_validated_citations: list[str] = []
        has_any_kb_citations = False

        for raw_finding in findings or []:
            finding_dict = (
                raw_finding.model_dump()
                if hasattr(raw_finding, "model_dump")
                else (
                    raw_finding
                    if isinstance(raw_finding, dict)
                    else vars(raw_finding)
                )
            )

            refs = finding_dict.get("evidence_refs", [])
            finding_invalid: list[str] = []
            finding_validated: list[str] = []

            for raw_ref in refs:
                ref = (
                    raw_ref.model_dump()
                    if hasattr(raw_ref, "model_dump")
                    else (
                        raw_ref
                        if isinstance(raw_ref, dict)
                        else vars(raw_ref)
                    )
                )

                source_type = str(ref.get("source_type") or "").upper()
                if source_type != "KNOWLEDGE_BASE":
                    continue

                has_any_kb_citations = True
                source_id = str(ref.get("source_id") or "").strip()

                if not source_id or source_id not in allowed_ids:
                    if source_id and source_id not in finding_invalid:
                        finding_invalid.append(source_id)
                        if source_id not in all_invalid_citations:
                            all_invalid_citations.append(source_id)
                    elif not source_id and "<EMPTY>" not in finding_invalid:
                        finding_invalid.append("<EMPTY>")
                        if "<EMPTY>" not in all_invalid_citations:
                            all_invalid_citations.append("<EMPTY>")
                else:
                    if source_id not in finding_validated:
                        finding_validated.append(source_id)
                    if source_id not in all_validated_citations:
                        all_validated_citations.append(source_id)

            if finding_invalid:
                reason = f"Finding referenced unknown citation(s): {', '.join(finding_invalid)}"
                findings_results.append(
                    FindingValidationResult(
                        valid=False,
                        invalid_citations=finding_invalid,
                        validated_citations=finding_validated,
                        reason=reason,
                    )
                )
            else:
                findings_results.append(
                    FindingValidationResult(
                        valid=True,
                        invalid_citations=[],
                        validated_citations=finding_validated,
                        reason=None,
                    )
                )

        if all_invalid_citations:
            grounding_status = "INVALID"
            overall_valid = False
            error_message = (
                f"Finding referenced unknown citation: {', '.join(all_invalid_citations)}"
            )
        elif has_rag_context or has_any_kb_citations:
            grounding_status = "VALID"
            overall_valid = True
            error_message = None
        else:
            grounding_status = "NOT_APPLICABLE"
            overall_valid = True
            error_message = None

        return GroundingValidationResult(
            valid=overall_valid,
            grounding_status=grounding_status,
            findings_results=findings_results,
            invalid_citations=all_invalid_citations,
            validated_citations=all_validated_citations,
            error_message=error_message,
        )

    def _extract_allowed_ids(self, rag_citations: list[Any]) -> set[str]:
        allowed = set()
        for raw_item in rag_citations or []:
            item = (
                raw_item.model_dump()
                if hasattr(raw_item, "model_dump")
                else (
                    raw_item
                    if isinstance(raw_item, dict)
                    else vars(raw_item)
                )
            )

            cit_id = item.get("citation_id")
            chunk_id = item.get("chunk_id")
            if cit_id:
                allowed.add(str(cit_id).strip())
            if chunk_id:
                allowed.add(str(chunk_id).strip())

        return allowed
