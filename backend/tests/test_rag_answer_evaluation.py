import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.ai.providers.base import LLMProvider
from app.ai.rag.evaluation.answer_runner import (
    RAGAnswerEvaluationRunner,
    is_fact_covered,
    is_forbidden_claim_present,
    load_answer_eval_cases,
)
from app.ai.rag.evaluation.answer_schemas import (
    AnswerGroundingTrace,
    RAGAnswerEvalCase,
    RAGAnswerEvalReport,
    RAGAnswerEvalResult,
)
from app.ai.rag.schemas import RetrievalResult
from app.ai.schemas.investigation_analysis import (
    EvidenceReference,
    InvestigationAnalysis,
    InvestigationFinding,
)


def _create_mock_llm_provider(
    summary: str,
    findings: list[InvestigationFinding],
    probable_root_cause: str | None = None,
    recommendations: list[str] | None = None,
) -> LLMProvider:
    provider = MagicMock(spec=LLMProvider)
    analysis = InvestigationAnalysis(
        summary=summary,
        findings=findings,
        probable_root_cause=probable_root_cause,
        recommendations=recommendations or [],
    )
    provider.generate.return_value = analysis.model_dump_json()
    return provider


# =========================================================================
# 1. Dataset Loading Tests
# =========================================================================

def test_answer_eval_dataset_loading():
    dataset_path = Path("knowledge/evaluation/rag_answer_eval_cases.json")
    if not dataset_path.exists():
        dataset_path = Path("../knowledge/evaluation/rag_answer_eval_cases.json")

    assert dataset_path.exists(), f"Missing dataset at {dataset_path}"
    version, cases = load_answer_eval_cases(dataset_path)

    assert version in ("1.0", "2.0")
    assert len(cases) >= 15, f"Expected at least 15 cases, got {len(cases)}"

    case_ids = set()
    for c in cases:
        assert c.case_id.startswith("ANS-")
        assert c.case_id not in case_ids, f"Duplicate case ID: {c.case_id}"
        case_ids.add(c.case_id)
        assert len(c.expected_facts) > 0
        assert len(c.forbidden_claims) > 0


# =========================================================================
# 2. Complete Answer Test
# =========================================================================

def test_complete_answer_evaluation():
    case = RAGAnswerEvalCase(
        case_id="ANS-001",
        category="root_cause_guidance",
        question="Why did payment timeouts occur?",
        expected_facts=[
            "Database connection timeout errors occurred in payment api",
            "Deployment version 2.8.1 modified connection pool configuration",
        ],
        expected_citations=["KB-1"],
        forbidden_claims=["Database server ran out of disk space"],
    )

    llm_provider = _create_mock_llm_provider(
        summary="Database connection timeout errors occurred in payment api after deployment version 2.8.1 modified connection pool configuration.",
        findings=[
            InvestigationFinding(
                finding="Deployment v2.8.1 reduced connection pool settings causing acquisition timeout errors.",
                confidence="HIGH",
                evidence_refs=[
                    EvidenceReference(source_type="KNOWLEDGE_BASE", source_id="KB-1"),
                ],
            )
        ],
        probable_root_cause="Deployment 2.8.1 pool exhaustion",
    )

    # Mock retrieval service returning KB-1
    mock_retrieval = MagicMock()
    mock_retrieval.retrieve_text.return_value = [
        RetrievalResult(
            chunk_id="chunk-1",
            document_id="doc-1",
            content="Payment API database runbook pool configuration",
            score=0.85,
            metadata={"source_name": "payment-api-database-timeouts.md", "source_type": "RUNBOOK"},
        )
    ]

    runner = RAGAnswerEvaluationRunner(
        llm_provider=llm_provider,
        retrieval_service=mock_retrieval,
    )

    result = runner.evaluate_case(case)

    assert result.citation_valid is True
    assert result.expected_facts_covered == 2
    assert result.completeness_score == 1.0
    assert result.unsupported_claim_count == 0
    assert result.grounding_score == 1.0
    assert result.passed is True
    assert "KB-1" in result.trace.used_citations


# =========================================================================
# 3. Partially Complete Answer Test
# =========================================================================

def test_partially_complete_answer():
    case = RAGAnswerEvalCase(
        case_id="ANS-002",
        category="root_cause_guidance",
        question="What caused payment timeouts?",
        expected_facts=[
            "Database connection timeout errors occurred in payment api",
            "Deployment version 2.8.1 modified connection pool configuration",
        ],
        forbidden_claims=[],
    )

    # Mentions timeout, but misses deployment correlation
    llm_provider = _create_mock_llm_provider(
        summary="Database connection timeout errors occurred in payment api.",
        findings=[
            InvestigationFinding(
                finding="Timeouts occurred during checkout.",
                confidence="MEDIUM",
                evidence_refs=[],
            )
        ],
    )

    runner = RAGAnswerEvaluationRunner(llm_provider=llm_provider)
    result = runner.evaluate_case(case)

    assert result.expected_facts_covered == 1
    assert result.expected_fact_count == 2
    assert result.completeness_score == 0.5
    assert len(result.trace.missing_facts) == 1


# =========================================================================
# 4. Missing Expected Fact Test
# =========================================================================

def test_missing_expected_fact():
    case = RAGAnswerEvalCase(
        case_id="ANS-003",
        category="symptom_lookup",
        question="What symptoms appeared?",
        expected_facts=["Connection wait time p99 increased significantly"],
        forbidden_claims=[],
    )

    llm_provider = _create_mock_llm_provider(
        summary="Unrelated information regarding user interface rendering.",
        findings=[],
    )

    runner = RAGAnswerEvaluationRunner(llm_provider=llm_provider)
    result = runner.evaluate_case(case)

    assert result.expected_facts_covered == 0
    assert result.completeness_score == 0.0
    assert result.passed is False


# =========================================================================
# 5. Invalid Citation Test (Crucial Grounding Check)
# =========================================================================

def test_invalid_citation_detected_and_fails_validity():
    """Model cites KB-99 when only KB-1 was retrieved -> citation_valid = False."""
    case = RAGAnswerEvalCase(
        case_id="ANS-004",
        category="runbook_lookup",
        question="What runbook steps exist?",
        expected_facts=[],
        forbidden_claims=[],
    )

    llm_provider = _create_mock_llm_provider(
        summary="Runbook guidelines apply.",
        findings=[
            InvestigationFinding(
                finding="Follow runbook procedure.",
                confidence="HIGH",
                evidence_refs=[
                    EvidenceReference(source_type="KNOWLEDGE_BASE", source_id="KB-99"),  # Unretrieved!
                ],
            )
        ],
    )

    # Only KB-1 was retrieved
    mock_retrieval = MagicMock()
    mock_retrieval.retrieve_text.return_value = [
        RetrievalResult(
            chunk_id="chunk-1",
            document_id="doc-1",
            content="Runbook content",
            score=0.88,
            metadata={"source_name": "payment.md"},
        )
    ]

    runner = RAGAnswerEvaluationRunner(
        llm_provider=llm_provider,
        retrieval_service=mock_retrieval,
    )
    result = runner.evaluate_case(case)

    assert result.citation_valid is False
    assert "KB-99" in result.trace.invalid_citations
    assert result.grounding_score == 0.0
    assert result.passed is False


# =========================================================================
# 6. Unsupported Claim Detection Test
# =========================================================================

def test_unsupported_claim_detection():
    """Model asserts a forbidden claim -> detected and fails grounding."""
    case = RAGAnswerEvalCase(
        case_id="ANS-005",
        category="root_cause_guidance",
        question="What caused the incident?",
        expected_facts=["Database connection timeouts occurred"],
        forbidden_claims=["The database server ran out of disk space"],
    )

    llm_provider = _create_mock_llm_provider(
        summary="Database connection timeouts occurred because the database server ran out of disk space.",
        findings=[
            InvestigationFinding(
                finding="The database server ran out of disk space causing crash.",
                confidence="HIGH",
                evidence_refs=[],
            )
        ],
    )

    runner = RAGAnswerEvaluationRunner(llm_provider=llm_provider)
    result = runner.evaluate_case(case)

    assert result.unsupported_claim_count == 1
    assert "The database server ran out of disk space" in result.trace.unsupported_claims
    assert result.grounding_score == 0.0
    assert result.passed is False


# =========================================================================
# 7. No-RAG Answer Test
# =========================================================================

def test_no_rag_answer_evaluation():
    case = RAGAnswerEvalCase(
        case_id="ANS-006",
        category="symptom_lookup",
        question="What happened?",
        expected_facts=["Elevated 5xx responses"],
        forbidden_claims=[],
    )

    llm_provider = _create_mock_llm_provider(
        summary="Elevated 5xx responses observed.",
        findings=[
            InvestigationFinding(
                finding="Elevated 5xx errors.",
                confidence="HIGH",
                evidence_refs=[EvidenceReference(source_type="incident_event", source_id="1")],
            )
        ],
    )

    # Retrieval service is None (incident evidence only)
    runner = RAGAnswerEvaluationRunner(
        llm_provider=llm_provider,
        retrieval_service=None,
    )
    result = runner.evaluate_case(case)

    assert result.citation_valid is True
    assert result.completeness_score == 1.0
    assert result.passed is True


# =========================================================================
# 8. Category Aggregation Test
# =========================================================================

def test_category_aggregation():
    cases = [
        RAGAnswerEvalCase(
            case_id="ANS-10",
            category="symptom_lookup",
            question="Q1",
            expected_facts=["Fact 1"],
            forbidden_claims=[],
        ),
        RAGAnswerEvalCase(
            case_id="ANS-11",
            category="root_cause_guidance",
            question="Q2",
            expected_facts=["Fact 2"],
            forbidden_claims=[],
        ),
    ]

    llm_provider = _create_mock_llm_provider(
        summary="Fact 1 and Fact 2 happened.",
        findings=[],
    )

    runner = RAGAnswerEvaluationRunner(llm_provider=llm_provider)
    report = runner.run_evaluation(cases)

    assert report.total_cases == 2
    assert "symptom_lookup" in report.category_metrics
    assert "root_cause_guidance" in report.category_metrics
    assert report.category_metrics["symptom_lookup"].case_count == 1
    assert report.category_metrics["root_cause_guidance"].case_count == 1
    assert report.citation_validity_rate == 1.0


# =========================================================================
# 9. Report Serialization Test
# =========================================================================

def test_report_serialization(tmp_path: Path):
    out_file = tmp_path / "answer_eval.json"
    case = RAGAnswerEvalCase(
        case_id="ANS-20",
        category="troubleshooting_procedure",
        question="How to fix?",
        expected_facts=["Roll back deployment"],
        forbidden_claims=[],
    )

    llm_provider = _create_mock_llm_provider(
        summary="Roll back deployment immediately.",
        findings=[],
    )

    runner = RAGAnswerEvaluationRunner(llm_provider=llm_provider)
    report = runner.run_evaluation([case], output_path=out_file)

    assert out_file.exists()
    loaded = json.loads(out_file.read_text(encoding="utf-8"))
    validated = RAGAnswerEvalReport.model_validate(loaded)
    assert validated.total_cases == 1
    assert validated.average_completeness == 1.0


# =========================================================================
# 10. Baseline vs Reranked Comparison Test
# =========================================================================

def test_baseline_vs_reranked_comparison():
    case = RAGAnswerEvalCase(
        case_id="ANS-30",
        category="runbook_lookup",
        question="What is the pool size?",
        expected_facts=["Standard pool size guidelines"],
        expected_citations=["KB-1"],
        forbidden_claims=[],
    )

    llm_provider = _create_mock_llm_provider(
        summary="Standard pool size guidelines in the runbook.",
        findings=[
            InvestigationFinding(
                finding="Pool size recommendation.",
                confidence="HIGH",
                evidence_refs=[EvidenceReference(source_type="KNOWLEDGE_BASE", source_id="KB-1")],
            )
        ],
    )

    mock_retrieval_a = MagicMock()
    mock_retrieval_a.retrieve_text.return_value = [
        RetrievalResult(chunk_id="c1", document_id="d1", content="Pool size", score=0.75, metadata={"source_name": "runbook.md"})
    ]

    mock_retrieval_b = MagicMock()
    mock_retrieval_b.retrieve_text.return_value = [
        RetrievalResult(chunk_id="c1", document_id="d1", content="Pool size", score=0.88, metadata={"source_name": "runbook.md"})
    ]

    runner_a = RAGAnswerEvaluationRunner(llm_provider=llm_provider, retrieval_service=mock_retrieval_a, pipeline_name="vector_only")
    runner_b = RAGAnswerEvaluationRunner(llm_provider=llm_provider, retrieval_service=mock_retrieval_b, pipeline_name="reranked")

    report_a = runner_a.run_evaluation([case])
    report_b = runner_b.run_evaluation([case])

    assert report_a.pipeline_name == "vector_only"
    assert report_b.pipeline_name == "reranked"
    assert report_a.citation_validity_rate == 1.0
    assert report_b.citation_validity_rate == 1.0
