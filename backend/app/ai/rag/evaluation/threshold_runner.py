from __future__ import annotations

import json
import logging
from collections import defaultdict
from pathlib import Path

from app.ai.rag.evaluation.runner import (
    AUTHORIZATION_CATEGORIES,
    NEGATIVE_CATEGORIES,
    POSITIVE_CATEGORIES,
    RAGEvaluationRunner,
)
from app.ai.rag.evaluation.schemas import EvalCase
from app.ai.rag.evaluation.threshold_schemas import (
    ScoreDistributionSummary,
    ThresholdSweepPoint,
    ThresholdSweepReport,
)
from app.ai.rag.retrieval.service import KnowledgeRetrievalService

logger = logging.getLogger(__name__)


def compute_score_distribution(scores: list[float]) -> ScoreDistributionSummary:
    if not scores:
        return ScoreDistributionSummary(
            min_score=None,
            max_score=None,
            mean_score=None,
            sample_count=0,
        )
    return ScoreDistributionSummary(
        min_score=round(min(scores), 4),
        max_score=round(max(scores), 4),
        mean_score=round(sum(scores) / len(scores), 4),
        sample_count=len(scores),
    )


class RAGThresholdSweepRunner:
    """Runs a controlled threshold sweep over RAG retrieval evaluation cases."""

    def __init__(
        self,
        retrieval_service: KnowledgeRetrievalService,
        top_k: int = 5,
        embedding_model: str = "gemini-embedding-2",
        embedding_dimensions: int = 1536,
    ) -> None:
        self.retrieval_service = retrieval_service
        self.top_k = top_k
        self.embedding_model = embedding_model
        self.embedding_dimensions = embedding_dimensions

    def select_threshold(
        self,
        points: list[ThresholdSweepPoint],
    ) -> tuple[float | None, str]:
        """
        Deterministic selection rule:
        1. Eligible threshold: positive Recall@K >= 1.0 and unauthorized_leakage_rate == 0.0
        2. Minimize unwanted_retrieval_rate
        3. Maximize clean_rejection_rate
        4. Lowest eligible threshold on tie
        """
        eligible = [
            p
            for p in points
            if p.positive_recall_at_k >= 1.0 and p.unauthorized_leakage_rate == 0.0
        ]

        if not eligible:
            return None, "No threshold preserved required positive recall."

        selected = sorted(
            eligible,
            key=lambda p: (
                p.unwanted_retrieval_rate,
                -p.clean_rejection_rate,
                p.threshold,
            ),
        )[0]

        reason = (
            f"Threshold {selected.threshold} selected: minimizes unwanted_retrieval_rate "
            f"({selected.unwanted_retrieval_rate}) and maximizes clean_rejection_rate "
            f"({selected.clean_rejection_rate}) while maintaining 100% positive recall."
        )
        return selected.threshold, reason

    def run_sweep(
        self,
        cases: list[EvalCase],
        *,
        dataset_version: str = "1.0",
        thresholds: list[float] | None = None,
        citation_grounding_rate: float = 1.0,
        output_path: Path | str | None = None,
    ) -> ThresholdSweepReport:
        if thresholds is None:
            thresholds = [0.25, 0.35, 0.45, 0.55, 0.65, 0.75]

        sweep_points: list[ThresholdSweepPoint] = []

        for threshold in thresholds:
            runner = RAGEvaluationRunner(
                retrieval_service=self.retrieval_service,
                top_k=self.top_k,
                score_threshold=threshold,
                embedding_model=self.embedding_model,
                embedding_dimensions=self.embedding_dimensions,
            )

            report = runner.run_evaluation(
                cases,
                dataset_version=dataset_version,
                citation_grounding_rate=citation_grounding_rate,
            )

            # Score distributions and retrieval counts
            pos_scores: list[float] = []
            neg_scores: list[float] = []
            category_counts: dict[str, int] = defaultdict(int)

            for cr in report.case_results:
                category_counts[cr.category] += len(cr.retrieved_documents)
                if cr.category in POSITIVE_CATEGORIES:
                    pos_scores.extend(cr.retrieved_scores)
                elif cr.category in NEGATIVE_CATEGORIES:
                    neg_scores.extend(cr.retrieved_scores)

            point = ThresholdSweepPoint(
                threshold=threshold,
                positive_case_count=report.positive_cases.count,
                positive_recall_at_k=report.positive_cases.recall_at_k,
                positive_precision_at_k=report.positive_cases.precision_at_k,
                positive_mrr=report.positive_cases.mrr,
                negative_case_count=report.negative_controls.count,
                unwanted_retrieval_rate=report.negative_controls.unwanted_retrieval_rate,
                clean_rejection_rate=report.negative_controls.clean_rejection_rate,
                authorization_case_count=report.authorization_cases.count,
                authorization_accuracy=report.authorization_cases.authorization_accuracy,
                unauthorized_leakage_rate=report.authorization_cases.unauthorized_leakage_rate,
                grounding_rate=report.grounding.citation_grounding_rate,
                positive_score_distribution=compute_score_distribution(pos_scores),
                negative_score_distribution=compute_score_distribution(neg_scores),
                category_retrieval_counts=dict(category_counts),
            )
            sweep_points.append(point)

        selected_threshold, selection_reason = self.select_threshold(sweep_points)

        report = ThresholdSweepReport(
            dataset_version=dataset_version,
            top_k=self.top_k,
            embedding_model=self.embedding_model,
            embedding_dimensions=self.embedding_dimensions,
            thresholds=sweep_points,
            selected_threshold=selected_threshold,
            selection_reason=selection_reason,
        )

        if output_path:
            p = Path(output_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            with p.open("w", encoding="utf-8") as f:
                f.write(report.model_dump_json(indent=2))
            logger.info("Persisted threshold sweep report to %s", p)

        return report
