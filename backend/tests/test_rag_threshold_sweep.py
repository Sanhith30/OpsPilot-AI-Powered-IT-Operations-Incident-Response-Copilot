import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.ai.rag.evaluation.schemas import EvalCase
from app.ai.rag.evaluation.threshold_runner import (
    RAGThresholdSweepRunner,
    compute_score_distribution,
)
from app.ai.rag.evaluation.threshold_schemas import (
    ScoreDistributionSummary,
    ThresholdSweepPoint,
    ThresholdSweepReport,
)
from app.ai.rag.retrieval.schemas import RetrievalFilters, RetrievalResponse
from app.ai.rag.schemas import RetrievalResult


def _create_mock_point(
    threshold: float,
    positive_recall: float,
    unwanted_rate: float,
    clean_rejection: float | None = None,
    leakage_rate: float = 0.0,
    auth_accuracy: float = 1.0,
) -> ThresholdSweepPoint:
    if clean_rejection is None:
        clean_rejection = round(1.0 - unwanted_rate, 4)
    return ThresholdSweepPoint(
        threshold=threshold,
        positive_case_count=16,
        positive_recall_at_k=positive_recall,
        positive_precision_at_k=1.0,
        positive_mrr=positive_recall,
        negative_case_count=6,
        unwanted_retrieval_rate=unwanted_rate,
        clean_rejection_rate=clean_rejection,
        authorization_case_count=3,
        authorization_accuracy=auth_accuracy,
        unauthorized_leakage_rate=leakage_rate,
        grounding_rate=1.0,
        positive_score_distribution=ScoreDistributionSummary(
            min_score=0.75, max_score=0.92, mean_score=0.85, sample_count=16
        ),
        negative_score_distribution=ScoreDistributionSummary(
            min_score=0.30, max_score=0.60, mean_score=0.45, sample_count=6
        ),
        category_retrieval_counts={"symptom_lookup": 4, "irrelevant_query": 2},
    )


def test_compute_score_distribution_empty_and_populated():
    empty_dist = compute_score_distribution([])
    assert empty_dist.min_score is None
    assert empty_dist.max_score is None
    assert empty_dist.mean_score is None
    assert empty_dist.sample_count == 0

    scores = [0.42, 0.88, 0.65]
    dist = compute_score_distribution(scores)
    assert dist.min_score == 0.42
    assert dist.max_score == 0.88
    assert dist.mean_score == round((0.42 + 0.88 + 0.65) / 3, 4)
    assert dist.sample_count == 3


def test_sweep_all_thresholds_evaluated(tmp_path: Path):
    """Test 1: Given [0.25, 0.35, 0.45, 0.55, 0.65, 0.75], verify six result rows."""
    mock_retrieval_service = MagicMock()
    mock_retrieval_service.retrieve.return_value = RetrievalResponse(
        query="test",
        results=[],
        result_count=0,
        applied_filters=RetrievalFilters(),
    )

    cases = [
        EvalCase(
            case_id="pos-1",
            query="kubernetes pod crash",
            category="symptom_lookup",
            expected_documents=["k8s-runbook"],
        )
    ]

    thresholds = [0.25, 0.35, 0.45, 0.55, 0.65, 0.75]
    runner = RAGThresholdSweepRunner(
        retrieval_service=mock_retrieval_service,
        top_k=5,
        embedding_model="gemini-embedding-2",
        embedding_dimensions=1536,
    )

    report = runner.run_sweep(
        cases,
        dataset_version="1.0",
        thresholds=thresholds,
    )

    assert len(report.thresholds) == 6
    assert [p.threshold for p in report.thresholds] == thresholds
    assert report.embedding_model == "gemini-embedding-2"
    assert report.top_k == 5


def test_selection_rule_preserves_positive_recall():
    """Test 2: Mock thresholds where 0.65 and 0.75 degrade recall. Selected cannot be 0.65 or 0.75."""
    runner = RAGThresholdSweepRunner(retrieval_service=MagicMock())

    points = [
        _create_mock_point(0.25, positive_recall=1.0, unwanted_rate=1.0),
        _create_mock_point(0.35, positive_recall=1.0, unwanted_rate=1.0),
        _create_mock_point(0.45, positive_recall=1.0, unwanted_rate=0.8),
        _create_mock_point(0.55, positive_recall=1.0, unwanted_rate=0.4),
        _create_mock_point(0.65, positive_recall=0.90, unwanted_rate=0.0),
        _create_mock_point(0.75, positive_recall=0.75, unwanted_rate=0.0),
    ]

    selected_threshold, reason = runner.select_threshold(points)
    assert selected_threshold == 0.55
    assert selected_threshold not in (0.65, 0.75)
    assert "minimizes unwanted_retrieval_rate (0.4)" in reason


def test_selection_rule_minimizes_unwanted_retrieval():
    """Test 3: Select threshold that minimizes unwanted retrieval while recall is 1.0."""
    runner = RAGThresholdSweepRunner(retrieval_service=MagicMock())

    points = [
        _create_mock_point(0.25, positive_recall=1.0, unwanted_rate=1.0),
        _create_mock_point(0.35, positive_recall=1.0, unwanted_rate=1.0),
        _create_mock_point(0.45, positive_recall=1.0, unwanted_rate=0.67),
        _create_mock_point(0.55, positive_recall=1.0, unwanted_rate=0.33),
        _create_mock_point(0.65, positive_recall=1.0, unwanted_rate=0.0),
        _create_mock_point(0.75, positive_recall=0.85, unwanted_rate=0.0),
    ]

    selected_threshold, reason = runner.select_threshold(points)
    assert selected_threshold == 0.65
    assert "minimizes unwanted_retrieval_rate (0.0)" in reason


def test_selection_rule_tie_breaker_selects_lowest():
    """Test 4: On equal unwanted retrieval and clean rejection, choose the lowest eligible threshold."""
    runner = RAGThresholdSweepRunner(retrieval_service=MagicMock())

    points = [
        _create_mock_point(0.55, positive_recall=1.0, unwanted_rate=0.0),
        _create_mock_point(0.65, positive_recall=1.0, unwanted_rate=0.0),
    ]

    selected_threshold, reason = runner.select_threshold(points)
    assert selected_threshold == 0.55


def test_selection_rule_no_eligible_threshold():
    """Test 5: Every threshold produces positive Recall@5 below 1.0."""
    runner = RAGThresholdSweepRunner(retrieval_service=MagicMock())

    points = [
        _create_mock_point(0.25, positive_recall=0.80, unwanted_rate=0.5),
        _create_mock_point(0.35, positive_recall=0.75, unwanted_rate=0.3),
        _create_mock_point(0.45, positive_recall=0.70, unwanted_rate=0.1),
    ]

    selected_threshold, reason = runner.select_threshold(points)
    assert selected_threshold is None
    assert reason == "No threshold preserved required positive recall."


def test_authorization_remains_isolated_and_strictly_checked():
    """Test 6: Authorization leakage disqualifies threshold, and auth checks don't corrupt recall."""
    runner = RAGThresholdSweepRunner(retrieval_service=MagicMock())

    # Point with 1.0 recall and 0.0 unwanted rate, but unauthorized leakage > 0
    points = [
        _create_mock_point(
            0.45,
            positive_recall=1.0,
            unwanted_rate=0.2,
            leakage_rate=0.0,
            auth_accuracy=1.0,
        ),
        _create_mock_point(
            0.55,
            positive_recall=1.0,
            unwanted_rate=0.0,
            leakage_rate=0.33,
            auth_accuracy=0.67,
        ),
    ]

    # 0.55 has lower unwanted rate but has leakage, so 0.45 must be chosen
    selected_threshold, reason = runner.select_threshold(points)
    assert selected_threshold == 0.45


def test_persisted_sweep_report_validates_against_pydantic(tmp_path: Path):
    """Test 7: Verify persisted sweep report validates against Pydantic schema."""
    output_file = tmp_path / "rag_threshold_sweep.json"

    points = [
        _create_mock_point(0.25, positive_recall=1.0, unwanted_rate=1.0),
        _create_mock_point(0.55, positive_recall=1.0, unwanted_rate=0.2),
    ]

    report = ThresholdSweepReport(
        dataset_version="1.0",
        top_k=5,
        embedding_model="gemini-embedding-2",
        embedding_dimensions=1536,
        thresholds=points,
        selected_threshold=0.55,
        selection_reason="Optimal point",
    )

    output_file.write_text(report.model_dump_json(indent=2), encoding="utf-8")

    # Read back and validate
    loaded_data = json.loads(output_file.read_text(encoding="utf-8"))
    validated = ThresholdSweepReport.model_validate(loaded_data)
    assert validated.dataset_version == "1.0"
    assert validated.selected_threshold == 0.55
    assert len(validated.thresholds) == 2
    assert validated.thresholds[0].positive_score_distribution.sample_count == 16
