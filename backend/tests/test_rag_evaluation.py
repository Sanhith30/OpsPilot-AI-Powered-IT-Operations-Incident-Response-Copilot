import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.ai.rag.evaluation.metrics import (
    calculate_authorization_accuracy,
    calculate_grounding_rate,
    calculate_mrr,
    calculate_precision_at_k,
    calculate_recall_at_k,
    calculate_reciprocal_rank,
    calculate_unauthorized_leakage_rate,
    calculate_unwanted_retrieval_rate,
)
from app.ai.rag.evaluation.runner import (
    RAGEvaluationRunner,
    load_eval_cases,
)
from app.ai.rag.evaluation.schemas import (
    EvalCase,
    EvaluationReport,
)
from app.ai.rag.retrieval.schemas import (
    RetrievalFilters,
    RetrievalResponse,
)
from app.ai.rag.retrieval.service import KnowledgeRetrievalService
from app.ai.rag.schemas import RetrievalResult


# =========================================================================
# 1. Dataset Structure and Integrity Tests
# =========================================================================

def test_evaluation_dataset_loading_and_structure():
    dataset_path = Path("knowledge/evaluation/rag_eval_cases.json")
    if not dataset_path.exists():
        dataset_path = Path("../knowledge/evaluation/rag_eval_cases.json")

    assert dataset_path.exists(), f"Dataset file missing at {dataset_path}"

    dataset_version, cases = load_eval_cases(dataset_path)
    assert dataset_version in ("1.0", "2.0")
    assert len(cases) >= 20, f"Expected at least 20 cases, found {len(cases)}"

    case_ids = set()
    categories = set()
    for case in cases:
        assert case.case_id.startswith("RAG-")
        assert case.case_id not in case_ids, f"Duplicate case ID: {case.case_id}"
        case_ids.add(case.case_id)

        assert len(case.query.strip()) > 0
        assert case.expected_access in {"ALLOWED", "DENIED"}
        categories.add(case.category)

    # Must cover the expected evaluation categories
    expected_categories = {
        "symptom_lookup",
        "root_cause_guidance",
        "troubleshooting_procedure",
        "runbook_lookup",
        "irrelevant_query",
        "ambiguous_query",
        "no_answer_query",
        "authorization_control",
    }
    assert expected_categories.issubset(categories)


# =========================================================================
# 2. Metric Calculation Unit Tests
# =========================================================================

def test_recall_at_k():
    # Full match
    assert calculate_recall_at_k(["doc1.md"], ["doc1.md", "doc2.md"]) == 1.0
    # Complete miss
    assert calculate_recall_at_k(["doc1.md"], ["doc2.md", "doc3.md"]) == 0.0
    # Partial match
    assert calculate_recall_at_k(["doc1.md", "doc2.md"], ["doc1.md"]) == 0.5
    # Empty expected
    assert calculate_recall_at_k([], []) == 0.0


def test_precision_at_k():
    # 1 of 2 retrieved is relevant
    assert calculate_precision_at_k(["doc1.md"], ["doc1.md", "doc2.md"]) == 0.5
    # 1 of 1 retrieved is relevant
    assert calculate_precision_at_k(["doc1.md"], ["doc1.md"]) == 1.0
    # 0 of 2 retrieved are relevant
    assert calculate_precision_at_k(["doc1.md"], ["doc2.md", "doc3.md"]) == 0.0
    # Empty retrieved
    assert calculate_precision_at_k(["doc1.md"], []) == 0.0


def test_reciprocal_rank_and_mrr():
    # Rank 1
    assert calculate_reciprocal_rank(["doc1.md"], ["doc1.md", "doc2.md"]) == 1.0
    # Rank 2
    assert calculate_reciprocal_rank(["doc1.md"], ["doc2.md", "doc1.md"]) == 0.5
    # Rank 3
    assert (
        calculate_reciprocal_rank(["doc1.md"], ["doc2.md", "doc3.md", "doc1.md"])
        == pytest.approx(1.0 / 3)
    )
    # Not found
    assert calculate_reciprocal_rank(["doc1.md"], ["doc2.md", "doc3.md"]) == 0.0

    # MRR calculation
    assert calculate_mrr([1.0, 0.5, 0.0]) == 0.5
    assert calculate_mrr([]) == 0.0


def test_negative_control_metrics():
    # 2 out of 4 queries retrieved unwanted results
    flags = [True, False, True, False]
    assert calculate_unwanted_retrieval_rate(flags) == 0.5
    assert calculate_unwanted_retrieval_rate([True, True, True]) == 1.0
    assert calculate_unwanted_retrieval_rate([False, False]) == 0.0
    assert calculate_unwanted_retrieval_rate([]) == 0.0


def test_authorization_accuracy_and_leakage():
    assert calculate_authorization_accuracy([True, True, True, True]) == 1.0
    assert calculate_authorization_accuracy([True, False, True, False]) == 0.5
    assert calculate_authorization_accuracy([]) == 1.0

    # Leakage rate
    assert calculate_unauthorized_leakage_rate([True, False]) == 0.5
    assert calculate_unauthorized_leakage_rate([False, False]) == 0.0
    assert calculate_unauthorized_leakage_rate([]) == 0.0


def test_grounding_rate():
    assert calculate_grounding_rate(10, 10) == 1.0
    assert calculate_grounding_rate(8, 10) == 0.8
    assert calculate_grounding_rate(0, 0) == 1.0


# =========================================================================
# 3. Runner Evaluation with Mock Retrieval Service
# =========================================================================

def test_runner_evaluates_allowed_positive_case():
    mock_retrieval = MagicMock(spec=KnowledgeRetrievalService)
    mock_retrieval.retrieve.return_value = RetrievalResponse(
        query="timeout test",
        results=[
            RetrievalResult(
                chunk_id="c1",
                document_id="d1",
                content="Contains database timeout details.",
                score=0.88,
                metadata={"source_name": "payment-api-database-timeouts.md"},
            )
        ],
        result_count=1,
        applied_filters=RetrievalFilters(),
    )

    runner = RAGEvaluationRunner(
        retrieval_service=mock_retrieval,
        top_k=5,
        score_threshold=0.35,
    )

    case = EvalCase(
        case_id="TEST-001",
        query="What are database timeout symptoms?",
        category="symptom_lookup",
        expected_documents=["payment-api-database-timeouts.md"],
        expected_keywords=["timeout"],
        user_id=1,
        team_id=1,
        expected_access="ALLOWED",
    )

    res = runner.evaluate_case(case)
    assert res.case_id == "TEST-001"
    assert res.recall_at_k == 1.0
    assert res.precision_at_k == 1.0
    assert res.reciprocal_rank == 1.0
    assert "timeout" in res.keywords_found


def test_runner_evaluates_negative_control_case():
    mock_retrieval = MagicMock(spec=KnowledgeRetrievalService)
    # Simulated unwanted retrieval for irrelevant query
    mock_retrieval.retrieve.return_value = RetrievalResponse(
        query="lunch menu",
        results=[
            RetrievalResult(
                chunk_id="c1",
                document_id="d1",
                content="Irrelevant match content",
                score=0.40,
                metadata={"source_name": "payment-api-database-timeouts.md"},
            )
        ],
        result_count=1,
        applied_filters=RetrievalFilters(),
    )

    runner = RAGEvaluationRunner(
        retrieval_service=mock_retrieval,
        top_k=5,
        score_threshold=0.35,
    )

    case = EvalCase(
        case_id="TEST-IRR",
        query="What is the lunch menu?",
        category="irrelevant_query",
        expected_documents=[],
        user_id=1,
        team_id=1,
        expected_access="ALLOWED",
    )

    res = runner.evaluate_case(case)
    assert res.unwanted_retrieval is True
    assert res.recall_at_k is None  # Not polluted by recall calculation


def test_runner_evaluates_denied_authorization_case():
    mock_retrieval = MagicMock(spec=KnowledgeRetrievalService)
    # The retrieval service correctly withheld the unauthorized document
    mock_retrieval.retrieve.return_value = RetrievalResponse(
        query="secret query",
        results=[],
        result_count=0,
        applied_filters=RetrievalFilters(),
    )

    runner = RAGEvaluationRunner(
        retrieval_service=mock_retrieval,
        top_k=5,
        score_threshold=0.35,
    )

    case = EvalCase(
        case_id="TEST-AUTH-DENIED",
        query="Access secret document",
        category="authorization_control",
        expected_documents=["secret-runbook.md"],
        user_id=2,
        team_id=2,
        expected_access="DENIED",
    )

    res = runner.evaluate_case(case)
    # Because expected_access == "DENIED" and secret-runbook.md was NOT returned:
    assert res.access_passed is True
    assert res.retrieved_documents == []


def test_runner_detects_unauthorized_leakage():
    mock_retrieval = MagicMock(spec=KnowledgeRetrievalService)
    # The retrieval service leaked an unauthorized document
    mock_retrieval.retrieve.return_value = RetrievalResponse(
        query="secret query",
        results=[
            RetrievalResult(
                chunk_id="c_secret",
                document_id="d_secret",
                content="Top secret credential text",
                score=0.95,
                metadata={"source_name": "secret-runbook.md"},
            )
        ],
        result_count=1,
        applied_filters=RetrievalFilters(),
    )

    runner = RAGEvaluationRunner(
        retrieval_service=mock_retrieval,
        top_k=5,
        score_threshold=0.35,
    )

    case = EvalCase(
        case_id="TEST-LEAK",
        query="Access secret document",
        category="authorization_control",
        expected_documents=["secret-runbook.md"],
        user_id=2,
        team_id=2,
        expected_access="DENIED",
    )

    res = runner.evaluate_case(case)
    # Leakage must fail the access check!
    assert res.access_passed is False
    assert "secret-runbook.md" in res.retrieved_documents


def test_runner_run_evaluation_population_aggregation(tmp_path):
    mock_retrieval = MagicMock(spec=KnowledgeRetrievalService)
    mock_retrieval.retrieve.return_value = RetrievalResponse(
        query="test",
        results=[
            RetrievalResult(
                chunk_id="c1",
                document_id="d1",
                content="Sample content",
                score=0.8,
                metadata={"source_name": "doc1.md"},
            )
        ],
        result_count=1,
        applied_filters=RetrievalFilters(),
    )

    runner = RAGEvaluationRunner(
        retrieval_service=mock_retrieval,
        top_k=5,
        score_threshold=0.35,
    )

    cases = [
        # Positive case: hit
        EvalCase(
            case_id="P1",
            query="q1",
            category="symptom_lookup",
            expected_documents=["doc1.md"],
            expected_access="ALLOWED",
        ),
        # Negative control: unwanted retrieval since doc1.md was returned
        EvalCase(
            case_id="N1",
            query="irrelevant",
            category="irrelevant_query",
            expected_documents=[],
            expected_access="ALLOWED",
        ),
        # Authorization case: doc1.md was returned, which leaks doc1.md!
        EvalCase(
            case_id="A1",
            query="auth denied test",
            category="authorization_control",
            expected_documents=["doc1.md"],
            expected_access="DENIED",
        ),
    ]

    out_file = tmp_path / "test_report.json"
    report = runner.run_evaluation(
        cases,
        dataset_version="1.0-test",
        citation_grounding_rate=0.95,
        output_path=out_file,
    )

    # Positive population
    assert report.positive_cases.count == 1
    assert report.positive_cases.recall_at_k == 1.0
    assert report.positive_cases.precision_at_k == 1.0
    assert report.positive_cases.mrr == 1.0

    # Negative population
    assert report.negative_controls.count == 1
    assert report.negative_controls.unwanted_retrieval_rate == 1.0
    assert report.negative_controls.clean_rejection_rate == 0.0

    # Authorization population
    assert report.authorization_cases.count == 1
    assert report.authorization_cases.authorization_accuracy == 0.0
    assert report.authorization_cases.unauthorized_leakage_rate == 1.0

    # Grounding population
    assert report.grounding.citation_grounding_rate == 0.95

    assert out_file.exists()


# =========================================================================
# 4. Artifact Validation Test
# =========================================================================

def test_persisted_rag_evaluation_artifact_valid():
    report_path = Path("reports/rag_evaluation_latest.json")
    if not report_path.exists():
        report_path = Path("../reports/rag_evaluation_latest.json")

    assert report_path.exists(), f"Evaluation artifact report missing at {report_path}"

    with report_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    report = EvaluationReport.model_validate(data)
    assert report.dataset_version == "1.0"
    assert report.total_cases == 25
    assert report.top_k == 5
    assert report.retrieval_threshold == 0.35
    assert report.embedding_model == "gemini-embedding-2"
    assert report.embedding_dimensions == 1536

    # Verify separate population metrics
    assert report.positive_cases.count == 16
    assert report.positive_cases.recall_at_k == 1.0
    assert report.positive_cases.precision_at_k == 1.0
    assert report.positive_cases.mrr == 1.0

    assert report.negative_controls.count == 6
    assert report.negative_controls.unwanted_retrieval_rate == 1.0
    assert report.negative_controls.clean_rejection_rate == 0.0

    assert report.authorization_cases.count == 3
    assert report.authorization_cases.authorization_accuracy == 1.0
    assert report.authorization_cases.unauthorized_leakage_rate == 0.0

    assert report.grounding.citation_grounding_rate == 1.0
    assert len(report.case_results) == 25
