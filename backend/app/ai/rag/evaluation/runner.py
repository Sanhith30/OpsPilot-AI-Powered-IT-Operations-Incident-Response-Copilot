from __future__ import annotations

import json
import logging
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from app.ai.rag.access.policy import KnowledgeAccessContext
from app.ai.rag.evaluation.document_metrics import (
    ChunkRetrievalMetrics,
    DocumentRetrievalMetrics,
    calculate_chunk_precision_at_k,
    calculate_chunk_recall_at_k,
    calculate_chunk_reciprocal_rank,
    calculate_document_mrr,
    calculate_document_precision_at_k,
    calculate_document_recall_at_k,
    calculate_document_reciprocal_rank,
    extract_document_diagnostics,
    unique_documents,
)
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
from app.ai.rag.evaluation.schemas import (
    AuthorizationMetrics,
    CategoryMetric,
    EvalCase,
    EvalCaseResult,
    EvaluationReport,
    GroundingMetrics,
    NegativeControlMetrics,
    PositiveRetrievalMetrics,
)
from app.ai.rag.retrieval.schemas import RetrievalQuery
from app.ai.rag.retrieval.service import KnowledgeRetrievalService


logger = logging.getLogger(__name__)

POSITIVE_CATEGORIES = {
    "symptom_lookup",
    "root_cause_guidance",
    "troubleshooting_procedure",
    "troubleshooting",
    "runbook_lookup",
    "service_specific_lookup",
    "cross_document_disambiguation",
    "deployment_correlation",
    "postmortem_lookup",
}

NEGATIVE_CATEGORIES = {
    "irrelevant_query",
    "ambiguous_query",
    "no_answer_query",
}

AUTHORIZATION_CATEGORIES = {
    "authorization_control",
}


def load_eval_cases(file_path: Path | str) -> tuple[str, list[EvalCase]]:
    """Load evaluation cases from a JSON benchmark file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Evaluation benchmark file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    dataset_version = data.get("dataset_version", "1.0")
    raw_cases = data.get("cases", [])
    cases = [EvalCase.model_validate(c) for c in raw_cases]
    return dataset_version, cases


class RAGEvaluationRunner:

    def __init__(
        self,
        retrieval_service: KnowledgeRetrievalService,
        top_k: int = 5,
        score_threshold: float = 0.35,
        embedding_model: str = "gemini-embedding-2",
        embedding_dimensions: int = 1536,
    ) -> None:
        self.retrieval_service = retrieval_service
        self.top_k = top_k
        self.score_threshold = score_threshold
        self.embedding_model = embedding_model
        self.embedding_dimensions = embedding_dimensions

    def evaluate_case(self, case: EvalCase) -> EvalCaseResult:
        context = KnowledgeAccessContext(
            user_id=case.user_id,
            team_id=case.team_id,
        )

        query_request = RetrievalQuery(
            query=case.query,
            top_k=self.top_k,
            score_threshold=self.score_threshold,
        )

        response = self.retrieval_service.retrieve(
            query_request,
            context=context,
        )

        # Extract raw chunks and aggregated unique documents
        retrieved_chunks: list[str] = []
        retrieved_scores: list[float] = []
        for r in response.results:
            source_name = r.metadata.get("source_name") or r.document_id
            retrieved_chunks.append(source_name)
            if hasattr(r, "score") and r.score is not None:
                retrieved_scores.append(round(float(r.score), 4))

        aggregated_docs = unique_documents(response.results)
        retrieved_documents = [d.source_name for d in aggregated_docs]

        # Extract document-ranking diagnostics
        diag = extract_document_diagnostics(
            expected_documents=case.expected_documents,
            aggregated_docs=aggregated_docs,
            chunk_sources=retrieved_chunks,
        )

        # Keyword verification across retrieved chunk text
        keywords_found: list[str] = []
        for kw in case.expected_keywords:
            if any(kw.lower() in r.content.lower() for r in response.results):
                keywords_found.append(kw)

        # Separate population evaluations
        recall: float | None = None
        precision: float | None = None
        rr: float | None = None
        chunk_recall: float | None = None
        chunk_precision: float | None = None
        chunk_rr: float | None = None
        doc_recall: float | None = None
        doc_precision: float | None = None
        doc_rr: float | None = None
        unwanted_retrieval: bool | None = None
        access_passed: bool | None = None

        if case.category in POSITIVE_CATEGORIES:
            # Document-level metrics
            doc_recall = round(
                calculate_document_recall_at_k(case.expected_documents, retrieved_documents),
                4,
            )
            doc_precision = round(
                calculate_document_precision_at_k(case.expected_documents, retrieved_documents),
                4,
            )
            doc_rr = round(
                calculate_document_reciprocal_rank(case.expected_documents, retrieved_documents),
                4,
            )

            # Chunk-level metrics
            chunk_recall = round(
                calculate_chunk_recall_at_k(case.expected_documents, retrieved_chunks),
                4,
            )
            chunk_precision = round(
                calculate_chunk_precision_at_k(case.expected_documents, retrieved_chunks),
                4,
            )
            chunk_rr = round(
                calculate_chunk_reciprocal_rank(case.expected_documents, retrieved_chunks),
                4,
            )

            # Preserved general fields
            recall = doc_recall
            precision = doc_precision
            rr = doc_rr

        elif case.category in NEGATIVE_CATEGORIES:
            # Negative control: unwanted if any document was surfaced
            unwanted_retrieval = len(retrieved_documents) > 0

        elif case.category in AUTHORIZATION_CATEGORIES:
            if case.expected_access == "DENIED":
                # Must NOT leak restricted document
                access_passed = not any(
                    doc in retrieved_documents for doc in case.expected_documents
                )
            else:
                access_passed = any(
                    doc in retrieved_documents for doc in case.expected_documents
                )
            # We can also measure recall for allowed auth cases
            if case.expected_documents:
                recall = round(
                    calculate_document_recall_at_k(
                        case.expected_documents, retrieved_documents
                    ),
                    4,
                )

        return EvalCaseResult(
            case_id=case.case_id,
            query=case.query,
            category=case.category,
            expected_documents=case.expected_documents,
            retrieved_documents=retrieved_documents,
            retrieved_scores=retrieved_scores,
            recall_at_k=recall,
            precision_at_k=precision,
            reciprocal_rank=rr,
            retrieved_chunks=retrieved_chunks,
            chunk_recall_at_k=chunk_recall,
            chunk_precision_at_k=chunk_precision,
            chunk_reciprocal_rank=chunk_rr,
            document_recall_at_k=doc_recall,
            document_precision_at_k=doc_precision,
            document_reciprocal_rank=doc_rr,
            expected_document_rank=diag.expected_document_rank,
            best_chunk_rank=diag.best_chunk_rank,
            unique_document_count=diag.unique_document_count,
            target_document_present=diag.target_document_present,
            unwanted_retrieval=unwanted_retrieval,
            expected_access=case.expected_access,
            access_passed=access_passed,
            keywords_found=keywords_found,
        )

    def run_evaluation(
        self,
        cases: list[EvalCase],
        *,
        dataset_version: str = "1.0",
        citation_grounding_rate: float = 1.0,
        output_path: Path | str | None = None,
    ) -> EvaluationReport:
        case_results: list[EvalCaseResult] = []
        for c in cases:
            res = self.evaluate_case(c)
            case_results.append(res)

        # 1. Positive retrieval metrics population
        positive_results = [
            r for r in case_results if r.category in POSITIVE_CATEGORIES
        ]
        if positive_results:
            pos_recalls = [
                r.recall_at_k for r in positive_results if r.recall_at_k is not None
            ]
            pos_precisions = [
                r.precision_at_k
                for r in positive_results
                if r.precision_at_k is not None
            ]
            pos_rrs = [
                r.reciprocal_rank
                for r in positive_results
                if r.reciprocal_rank is not None
            ]
            pos_metrics = PositiveRetrievalMetrics(
                count=len(positive_results),
                recall_at_k=round(
                    sum(pos_recalls) / len(pos_recalls) if pos_recalls else 0.0,
                    4,
                ),
                precision_at_k=round(
                    sum(pos_precisions) / len(pos_precisions)
                    if pos_precisions
                    else 0.0,
                    4,
                ),
                mrr=round(calculate_mrr(pos_rrs), 4),
            )

            # Document-level metrics
            doc_recalls = [
                r.document_recall_at_k
                for r in positive_results
                if r.document_recall_at_k is not None
            ]
            doc_precisions = [
                r.document_precision_at_k
                for r in positive_results
                if r.document_precision_at_k is not None
            ]
            doc_rrs = [
                r.document_reciprocal_rank
                for r in positive_results
                if r.document_reciprocal_rank is not None
            ]
            doc_metrics = DocumentRetrievalMetrics(
                count=len(positive_results),
                recall_at_k=round(
                    sum(doc_recalls) / len(doc_recalls) if doc_recalls else 0.0,
                    4,
                ),
                precision_at_k=round(
                    sum(doc_precisions) / len(doc_precisions)
                    if doc_precisions
                    else 0.0,
                    4,
                ),
                mrr=round(calculate_document_mrr(doc_rrs), 4),
            )

            # Chunk-level metrics
            chk_recalls = [
                r.chunk_recall_at_k
                for r in positive_results
                if r.chunk_recall_at_k is not None
            ]
            chk_precisions = [
                r.chunk_precision_at_k
                for r in positive_results
                if r.chunk_precision_at_k is not None
            ]
            chk_rrs = [
                r.chunk_reciprocal_rank
                for r in positive_results
                if r.chunk_reciprocal_rank is not None
            ]
            chk_metrics = ChunkRetrievalMetrics(
                count=len(positive_results),
                recall_at_k=round(
                    sum(chk_recalls) / len(chk_recalls) if chk_recalls else 0.0,
                    4,
                ),
                precision_at_k=round(
                    sum(chk_precisions) / len(chk_precisions)
                    if chk_precisions
                    else 0.0,
                    4,
                ),
                mrr=round(calculate_document_mrr(chk_rrs), 4),
            )
        else:
            pos_metrics = PositiveRetrievalMetrics(
                count=0,
                recall_at_k=0.0,
                precision_at_k=0.0,
                mrr=0.0,
            )
            doc_metrics = DocumentRetrievalMetrics(
                count=0,
                recall_at_k=0.0,
                precision_at_k=0.0,
                mrr=0.0,
            )
            chk_metrics = ChunkRetrievalMetrics(
                count=0,
                recall_at_k=0.0,
                precision_at_k=0.0,
                mrr=0.0,
            )

        # 2. Negative control metrics population
        negative_results = [
            r for r in case_results if r.category in NEGATIVE_CATEGORIES
        ]
        if negative_results:
            unwanted_flags = [
                bool(r.unwanted_retrieval) for r in negative_results
            ]
            unwanted_rate = round(
                calculate_unwanted_retrieval_rate(unwanted_flags), 4
            )
            neg_metrics = NegativeControlMetrics(
                count=len(negative_results),
                unwanted_retrieval_rate=unwanted_rate,
                clean_rejection_rate=round(1.0 - unwanted_rate, 4),
            )
        else:
            neg_metrics = NegativeControlMetrics(
                count=0,
                unwanted_retrieval_rate=0.0,
                clean_rejection_rate=1.0,
            )

        # 3. Authorization metrics population
        auth_results = [
            r for r in case_results if r.category in AUTHORIZATION_CATEGORIES
        ]
        if auth_results:
            auth_checks = [
                bool(r.access_passed)
                for r in auth_results
                if r.access_passed is not None
            ]
            auth_acc = round(
                calculate_authorization_accuracy(auth_checks), 4
            )
            denied_cases = [
                r for r in auth_results if r.expected_access == "DENIED"
            ]
            leakage_flags = [
                not r.access_passed
                for r in denied_cases
                if r.access_passed is not None
            ]
            leak_rate = round(
                calculate_unauthorized_leakage_rate(leakage_flags), 4
            )
            auth_metrics = AuthorizationMetrics(
                count=len(auth_results),
                authorization_accuracy=auth_acc,
                unauthorized_leakage_rate=leak_rate,
            )
        else:
            auth_metrics = AuthorizationMetrics(
                count=0,
                authorization_accuracy=1.0,
                unauthorized_leakage_rate=0.0,
            )

        # 4. Grounding metrics population
        grounding_metrics = GroundingMetrics(
            citation_grounding_rate=round(citation_grounding_rate, 4),
        )

        # 5. Category-level breakdowns
        cat_grouped: dict[str, list[EvalCaseResult]] = defaultdict(list)
        for r in case_results:
            cat_grouped[r.category].append(r)

        category_metrics: dict[str, CategoryMetric] = {}
        for cat, results in cat_grouped.items():
            if cat in POSITIVE_CATEGORIES:
                c_recalls = [
                    r.recall_at_k for r in results if r.recall_at_k is not None
                ]
                c_precisions = [
                    r.precision_at_k
                    for r in results
                    if r.precision_at_k is not None
                ]
                c_rrs = [
                    r.reciprocal_rank
                    for r in results
                    if r.reciprocal_rank is not None
                ]
                c_doc_recalls = [
                    r.document_recall_at_k
                    for r in results
                    if r.document_recall_at_k is not None
                ]
                c_doc_precisions = [
                    r.document_precision_at_k
                    for r in results
                    if r.document_precision_at_k is not None
                ]
                c_doc_rrs = [
                    r.document_reciprocal_rank
                    for r in results
                    if r.document_reciprocal_rank is not None
                ]
                c_chk_recalls = [
                    r.chunk_recall_at_k
                    for r in results
                    if r.chunk_recall_at_k is not None
                ]
                c_chk_precisions = [
                    r.chunk_precision_at_k
                    for r in results
                    if r.chunk_precision_at_k is not None
                ]
                c_chk_rrs = [
                    r.chunk_reciprocal_rank
                    for r in results
                    if r.chunk_reciprocal_rank is not None
                ]
                category_metrics[cat] = CategoryMetric(
                    case_count=len(results),
                    recall_at_k=round(
                        sum(c_recalls) / len(c_recalls) if c_recalls else 0.0,
                        4,
                    ),
                    precision_at_k=round(
                        sum(c_precisions) / len(c_precisions)
                        if c_precisions
                        else 0.0,
                        4,
                    ),
                    mrr=round(calculate_mrr(c_rrs), 4),
                    document_recall_at_k=round(
                        sum(c_doc_recalls) / len(c_doc_recalls) if c_doc_recalls else 0.0,
                        4,
                    ),
                    document_precision_at_k=round(
                        sum(c_doc_precisions) / len(c_doc_precisions) if c_doc_precisions else 0.0,
                        4,
                    ),
                    document_mrr=round(calculate_document_mrr(c_doc_rrs), 4),
                    chunk_recall_at_k=round(
                        sum(c_chk_recalls) / len(c_chk_recalls) if c_chk_recalls else 0.0,
                        4,
                    ),
                    chunk_precision_at_k=round(
                        sum(c_chk_precisions) / len(c_chk_precisions) if c_chk_precisions else 0.0,
                        4,
                    ),
                    chunk_mrr=round(calculate_document_mrr(c_chk_rrs), 4),
                )
            elif cat in NEGATIVE_CATEGORIES:
                unwanted_flags = [bool(r.unwanted_retrieval) for r in results]
                rate = round(
                    calculate_unwanted_retrieval_rate(unwanted_flags), 4
                )
                category_metrics[cat] = CategoryMetric(
                    case_count=len(results),
                    unwanted_retrieval_rate=rate,
                    clean_rejection_rate=round(1.0 - rate, 4),
                )
            elif cat in AUTHORIZATION_CATEGORIES:
                access_flags = [
                    bool(r.access_passed)
                    for r in results
                    if r.access_passed is not None
                ]
                denied_subset = [
                    r for r in results if r.expected_access == "DENIED"
                ]
                leak_flags = [
                    not r.access_passed
                    for r in denied_subset
                    if r.access_passed is not None
                ]
                category_metrics[cat] = CategoryMetric(
                    case_count=len(results),
                    authorization_accuracy=round(
                        calculate_authorization_accuracy(access_flags), 4
                    ),
                    unauthorized_leakage_rate=round(
                        calculate_unauthorized_leakage_rate(leak_flags), 4
                    ),
                )

        report = EvaluationReport(
            evaluation_timestamp=datetime.now(timezone.utc).isoformat(),
            dataset_version=dataset_version,
            total_cases=len(cases),
            top_k=self.top_k,
            retrieval_threshold=self.score_threshold,
            embedding_model=self.embedding_model,
            embedding_dimensions=self.embedding_dimensions,
            positive_cases=pos_metrics,
            chunk_metrics=chk_metrics,
            document_metrics=doc_metrics,
            negative_controls=neg_metrics,
            authorization_cases=auth_metrics,
            grounding=grounding_metrics,
            category_metrics=category_metrics,
            case_results=case_results,
        )

        if output_path is not None:
            out_file = Path(output_path)
            out_file.parent.mkdir(parents=True, exist_ok=True)
            with out_file.open("w", encoding="utf-8") as f:
                f.write(report.model_dump_json(indent=2))
            logger.info("Saved RAG evaluation report to %s", out_file)

        return report

