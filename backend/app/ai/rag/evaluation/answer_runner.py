from __future__ import annotations

import json
import logging
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from app.ai.graph.analysis_parser import parse_investigation_analysis
from app.ai.graph.prompts import build_investigation_prompt
from app.ai.providers.base import LLMProvider
from app.ai.rag.access.policy import KnowledgeAccessContext
from app.ai.rag.context.builder import RAGContextBuilder
from app.ai.rag.evaluation.answer_schemas import (
    AnswerGroundingTrace,
    RAGAnswerCategoryMetric,
    RAGAnswerEvalCase,
    RAGAnswerEvalReport,
    RAGAnswerEvalResult,
)
from app.ai.rag.retrieval.service import KnowledgeRetrievalService
from app.ai.rag.validation.citation_validator import CitationValidator
from app.ai.schemas.investigation_analysis import InvestigationAnalysis

logger = logging.getLogger(__name__)

STOP_WORDS = {
    "a", "an", "the", "in", "on", "at", "to", "for", "with", "by", "of",
    "from", "as", "is", "are", "was", "were", "be", "been", "it", "this",
    "that", "these", "those", "and", "or", "but", "not", "do", "does", "did",
}


def load_answer_eval_cases(file_path: Path | str) -> tuple[str, list[RAGAnswerEvalCase]]:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Answer evaluation cases not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    dataset_version = data.get("dataset_version", "1.0")
    cases = [RAGAnswerEvalCase.model_validate(c) for c in data.get("cases", [])]
    return dataset_version, cases


def extract_keywords(text: str) -> set[str]:
    tokens = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return {t for t in tokens if t not in STOP_WORDS and len(t) > 2}


def is_fact_covered(expected_fact: str, answer_text: str) -> bool:
    fact_tokens = extract_keywords(expected_fact)
    if not fact_tokens:
        return True

    answer_tokens = extract_keywords(answer_text)
    overlap = len(fact_tokens & answer_tokens) / len(fact_tokens)
    return overlap >= 0.50


def is_forbidden_claim_present(claim: str, text: str) -> bool:
    claim_tokens = extract_keywords(claim)
    if not claim_tokens:
        return False

    text_tokens = extract_keywords(text)
    overlap = len(claim_tokens & text_tokens) / len(claim_tokens)
    # If >= 75% of discriminating tokens of the forbidden claim appear together, it's detected
    return overlap >= 0.75


class RAGAnswerEvaluationRunner:
    """Evaluates LLM answer quality, groundedness, completeness, and unsupported claims."""

    def __init__(
        self,
        llm_provider: LLMProvider,
        retrieval_service: KnowledgeRetrievalService | None = None,
        rag_context_builder: RAGContextBuilder | None = None,
        citation_validator: CitationValidator | None = None,
        score_threshold: float = 0.65,
        top_k: int = 5,
        pipeline_name: str = "production",
    ) -> None:
        self.llm_provider = llm_provider
        self.retrieval_service = retrieval_service
        self.rag_context_builder = rag_context_builder or RAGContextBuilder()
        self.citation_validator = citation_validator or CitationValidator()
        self.score_threshold = score_threshold
        self.top_k = top_k
        self.pipeline_name = pipeline_name

    def evaluate_case(self, case: RAGAnswerEvalCase) -> RAGAnswerEvalResult:
        # 1. Retrieve knowledge context if retrieval service available
        rag_context_str: str | None = None
        rag_citations: list[dict[str, Any]] = []

        if self.retrieval_service is not None:
            results = self.retrieval_service.retrieve_text(
                case.question,
                context=KnowledgeAccessContext(
                    user_id=case.user_id,
                    team_id=case.team_id,
                ),
                top_k=self.top_k,
                score_threshold=self.score_threshold,
            )
            rag_ctx = self.rag_context_builder.build(
                query=case.question,
                results=results,
            )
            rag_context_str = rag_ctx.formatted_context
            rag_citations = [
                item.model_dump(mode="json")
                for item in rag_ctx.items
            ]

        # 2. Build production prompt and call LLM
        normalized_evidence: list[dict[str, Any]] = []
        for e in case.evidence:
            if isinstance(e, dict):
                e_copy = dict(e)
                if "title" not in e_copy:
                    e_copy["title"] = e_copy.get(
                        "summary",
                        f"{e_copy.get('source_type', 'evidence')} {e_copy.get('source_id', '')}",
                    )
                if "content" not in e_copy:
                    e_copy["content"] = e_copy.get(
                        "summary", e_copy.get("title", "Evidence details")
                    )
                normalized_evidence.append(e_copy)
            else:
                normalized_evidence.append(e)

        prompt = build_investigation_prompt(
            incident=case.incident,
            evidence=normalized_evidence,
            user_question=case.question,
            rag_context=rag_context_str,
        )

        raw_response = self.llm_provider.generate(
            system_prompt=(
                "You are an AI IT operations investigation assistant. "
                "Analyze incidents using only supplied evidence."
            ),
            user_prompt=prompt,
            temperature=0.0,
            response_schema=InvestigationAnalysis,
        )

        analysis = parse_investigation_analysis(raw_response)

        # 3. Citation validity check using CitationValidator
        validation_result = self.citation_validator.validate(
            analysis.findings,
            rag_citations,
        )

        used_citations = validation_result.validated_citations
        invalid_citations = validation_result.invalid_citations
        citation_valid = bool(validation_result.valid and not invalid_citations)

        # If case expects specific citations, verify they are cited
        if case.expected_citations:
            missing_expected = [
                c for c in case.expected_citations if c not in used_citations
            ]
            if missing_expected and not used_citations:
                citation_valid = False

        # 4. Factual completeness evaluation
        combined_text = (
            f"{analysis.summary} "
            + " ".join(f.finding for f in analysis.findings)
            + f" {analysis.probable_root_cause or ''} "
            + " ".join(analysis.recommendations)
        )

        covered_facts: list[str] = []
        missing_facts: list[str] = []

        for fact in case.expected_facts:
            if is_fact_covered(fact, combined_text):
                covered_facts.append(fact)
            else:
                missing_facts.append(fact)

        fact_count = len(case.expected_facts)
        completeness_score = (
            round(len(covered_facts) / max(fact_count, 1), 4)
            if fact_count > 0
            else 1.0
        )

        # 5. Unsupported-claim / hallucination detection
        unsupported_claims: list[str] = []
        for claim in case.forbidden_claims:
            if is_forbidden_claim_present(claim, combined_text):
                unsupported_claims.append(claim)

        # 6. Overall Grounding and Pass determination
        grounding_score = 1.0 if (citation_valid and not unsupported_claims) else 0.0
        passed = (
            citation_valid
            and completeness_score >= 0.65
            and len(unsupported_claims) == 0
        )

        trace = AnswerGroundingTrace(
            case_id=case.case_id,
            used_citations=used_citations,
            invalid_citations=invalid_citations,
            expected_facts_covered=covered_facts,
            missing_facts=missing_facts,
            unsupported_claims=unsupported_claims,
            answer_summary=analysis.summary,
            findings_count=len(analysis.findings),
        )

        return RAGAnswerEvalResult(
            case_id=case.case_id,
            category=case.category,
            citation_valid=citation_valid,
            expected_facts_covered=len(covered_facts),
            expected_fact_count=fact_count,
            completeness_score=completeness_score,
            unsupported_claim_count=len(unsupported_claims),
            grounding_score=grounding_score,
            passed=passed,
            trace=trace,
        )

    def run_evaluation(
        self,
        cases: list[RAGAnswerEvalCase],
        *,
        dataset_version: str = "1.0",
        output_path: Path | str | None = None,
    ) -> RAGAnswerEvalReport:
        results: list[RAGAnswerEvalResult] = []
        for c in cases:
            res = self.evaluate_case(c)
            results.append(res)

        total_cases = len(results)
        if total_cases == 0:
            return RAGAnswerEvalReport(
                dataset_version=dataset_version,
                total_cases=0,
                pipeline_name=self.pipeline_name,
                citation_validity_rate=0.0,
                average_completeness=0.0,
                grounding_rate=0.0,
                unsupported_claim_rate=0.0,
            )

        citation_valid_count = sum(1 for r in results if r.citation_valid)
        citation_validity_rate = round(citation_valid_count / total_cases, 4)

        avg_completeness = round(
            sum(r.completeness_score for r in results) / total_cases,
            4,
        )

        grounded_count = sum(1 for r in results if r.grounding_score > 0.0)
        grounding_rate = round(grounded_count / total_cases, 4)

        unsupported_count = sum(1 for r in results if r.unsupported_claim_count > 0)
        unsupported_claim_rate = round(unsupported_count / total_cases, 4)

        # Category breakdowns
        cat_groups: dict[str, list[RAGAnswerEvalResult]] = defaultdict(list)
        for r in results:
            cat_groups[r.category].append(r)

        category_metrics: dict[str, RAGAnswerCategoryMetric] = {}
        for cat, items in cat_groups.items():
            c_total = len(items)
            category_metrics[cat] = RAGAnswerCategoryMetric(
                case_count=c_total,
                citation_validity_rate=round(
                    sum(1 for i in items if i.citation_valid) / c_total, 4
                ),
                average_completeness=round(
                    sum(i.completeness_score for i in items) / c_total, 4
                ),
                grounding_rate=round(
                    sum(1 for i in items if i.grounding_score > 0.0) / c_total, 4
                ),
                unsupported_claim_rate=round(
                    sum(1 for i in items if i.unsupported_claim_count > 0) / c_total,
                    4,
                ),
                pass_rate=round(sum(1 for i in items if i.passed) / c_total, 4),
            )

        report = RAGAnswerEvalReport(
            dataset_version=dataset_version,
            total_cases=total_cases,
            pipeline_name=self.pipeline_name,
            citation_validity_rate=citation_validity_rate,
            average_completeness=avg_completeness,
            grounding_rate=grounding_rate,
            unsupported_claim_rate=unsupported_claim_rate,
            category_metrics=category_metrics,
            results=results,
        )

        if output_path is not None:
            out_file = Path(output_path)
            out_file.parent.mkdir(parents=True, exist_ok=True)
            with out_file.open("w", encoding="utf-8") as f:
                f.write(report.model_dump_json(indent=2))
            logger.info("Saved RAG answer evaluation report to %s", out_file)

        return report
