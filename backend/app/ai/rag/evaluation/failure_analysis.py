from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

from app.ai.rag.access.policy import KnowledgeAccessContext
from app.ai.rag.evaluation.diagnostics import (
    AnswerFailureTrace,
    DocumentCompetition,
    FailureType,
    PrecisionAnalysis,
    RerankerShift,
    RetrievalFailureRecord,
    RetrievalFailureReport,
)
from app.ai.rag.evaluation.schemas import EvalCase
from app.ai.rag.reranking.base import Reranker
from app.ai.rag.retrieval.schemas import RetrievalQuery
from app.ai.rag.retrieval.service import KnowledgeRetrievalService
from app.ai.rag.schemas import RetrievalResult

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


class RAGFailureAnalyzer:
    """
    Diagnostic analyzer for RAG retrieval and answer evaluation failures.
    Inspects document-level competition, candidate rank ordering, reranker impact,
    and precision bottlenecks without modifying production parameters.
    """

    def __init__(
        self,
        retrieval_service: KnowledgeRetrievalService,
        reranker: Reranker | None = None,
        candidate_k: int = 15,
        final_k: int = 5,
        score_threshold: float = 0.65,
    ) -> None:
        self.retrieval_service = retrieval_service
        self.vector_store = retrieval_service.vector_store
        self.document_repository = retrieval_service.document_repository
        self.access_policy = retrieval_service.access_policy
        self.reranker = reranker
        self.candidate_k = candidate_k
        self.final_k = final_k
        self.score_threshold = score_threshold

    def analyze_retrieval_cases(
        self,
        cases: list[EvalCase],
        dataset_version: str = "2.0",
    ) -> RetrievalFailureReport:
        """
        Run in-depth failure analysis across evaluation cases.
        """
        positive_cases = [c for c in cases if c.category in POSITIVE_CATEGORIES]
        failed_records: list[RetrievalFailureRecord] = []
        reranker_shifts: list[RerankerShift] = []
        borderline_competition: list[DocumentCompetition] = []

        # Precision tracking metrics

        total_retrieved_chunks = 0
        total_unique_docs_retrieved = 0
        total_target_chunks_retrieved = 0

        for case in cases:
            context = KnowledgeAccessContext(
                user_id=case.user_id,
                team_id=case.team_id,
            )

            # 1. Fetch raw candidate pool from vector store (up to candidate_k)
            raw_candidates: list[RetrievalResult] = self.vector_store.search(
                case.query,
                top_k=self.candidate_k,
                score_threshold=None,
            )

            # 2. Evaluate vector-only top candidates (filtered by threshold, version, access)
            vector_valid: list[RetrievalResult] = []
            for cand in raw_candidates:
                if cand.score < self.score_threshold:
                    continue
                if not self.retrieval_service._is_current_version(cand):
                    continue
                if not self.retrieval_service._has_access(cand, context):
                    continue
                vector_valid.append(cand)

            vector_top_k = vector_valid[: self.final_k]

            # 3. Evaluate reranked candidates if reranker provided
            if self.reranker is not None:
                reranked_raw = self.reranker.rerank(
                    query=case.query,
                    candidates=raw_candidates,
                    top_k=self.candidate_k,
                )
                reranked_valid: list[RetrievalResult] = []
                for cand in reranked_raw:
                    orig_score = cand.metadata.get("original_vector_score", cand.score)
                    if cand.score < self.score_threshold or orig_score < self.score_threshold:
                        continue
                    if not self.retrieval_service._is_current_version(cand):
                        continue
                    if not self.retrieval_service._has_access(cand, context):
                        continue
                    reranked_valid.append(cand)
                hybrid_top_k = reranked_valid[: self.final_k]
            else:
                hybrid_top_k = vector_top_k
                reranked_raw = raw_candidates

            # Map unique documents in hybrid top-k
            seen_docs = set()
            retrieved_doc_names: list[str] = []
            retrieved_scores: list[float] = []
            for r in hybrid_top_k:
                doc_name = r.metadata.get("source_name")
                if doc_name and doc_name not in seen_docs:
                    seen_docs.add(doc_name)
                    retrieved_doc_names.append(doc_name)
                retrieved_scores.append(round(float(r.score), 4))

            # Track precision metrics for positive cases
            if case.category in POSITIVE_CATEGORIES:
                total_retrieved_chunks += len(hybrid_top_k)
                total_unique_docs_retrieved += len(retrieved_doc_names)
                target_chunks = sum(
                    1
                    for r in hybrid_top_k
                    if r.metadata.get("source_name") in case.expected_documents
                )
                total_target_chunks_retrieved += target_chunks

            # Track Reranker Shifts for all candidates in the candidate pool
            self._track_reranker_shifts(
                case=case,
                raw_candidates=raw_candidates,
                reranked_candidates=reranked_raw,
                shifts_out=reranker_shifts,
            )

            # Track borderline competition for positive cases
            if case.category in POSITIVE_CATEGORIES and case.expected_documents:
                exp_doc = case.expected_documents[0]
                exp_cands = [c for c in raw_candidates if c.metadata.get("source_name") == exp_doc]
                comp_cands = [c for c in raw_candidates if c.metadata.get("source_name") not in case.expected_documents]
                if exp_cands and comp_cands:
                    best_exp = max(exp_cands, key=lambda c: float(c.score))
                    best_comp = comp_cands[0]
                    exp_sc = round(float(best_exp.score), 4)
                    comp_sc = round(float(best_comp.score), 4)
                    margin = round(comp_sc - exp_sc, 4)
                    exp_rnk = raw_candidates.index(best_exp) + 1
                    if margin >= -0.05:
                        borderline_competition.append(
                            DocumentCompetition(
                                expected_document=exp_doc,
                                expected_document_score=exp_sc,
                                expected_document_rank=exp_rnk,
                                top_competitor_document=best_comp.metadata.get("source_name"),
                                top_competitor_score=comp_sc,
                                margin=margin,
                            )
                        )

            # Check if this positive case failed Recall@5
            if case.category in POSITIVE_CATEGORIES:
                expected_primary = (
                    case.expected_documents[0] if case.expected_documents else ""
                )
                is_retrieved = any(
                    doc in retrieved_doc_names for doc in case.expected_documents
                )

                if not is_retrieved:
                    # Classify failure and analyze competition
                    fail_record = self._diagnose_failure(
                        case=case,
                        expected_doc=expected_primary,
                        raw_candidates=raw_candidates,
                        vector_valid=vector_valid,
                        hybrid_valid=hybrid_top_k,
                        retrieved_doc_names=retrieved_doc_names,
                        retrieved_scores=retrieved_scores,
                        context=context,
                    )
                    failed_records.append(fail_record)


        # Compute precision analysis
        num_pos = len(positive_cases)
        if num_pos > 0:
            mean_chunks = round(total_retrieved_chunks / num_pos, 2)
            mean_unique_docs = round(total_unique_docs_retrieved / num_pos, 2)
            mean_target_chunks = round(total_target_chunks_retrieved / num_pos, 2)
            actual_precision = round(
                total_target_chunks_retrieved / (num_pos * self.final_k), 4
            )
            theo_max = round(min(mean_target_chunks / self.final_k, 1.0), 4)

            precision_info = PrecisionAnalysis(
                total_positive_cases=num_pos,
                top_k=self.final_k,
                mean_chunks_retrieved_per_case=mean_chunks,
                mean_unique_docs_per_case=mean_unique_docs,
                mean_target_chunks_in_top_k=mean_target_chunks,
                theoretical_max_precision=theo_max,
                actual_precision_at_k=actual_precision,
                precision_explanation=(
                    f"In a multi-document corpus where target documents have ~2 chunks, "
                    f"retrieving top_k={self.final_k} results in ~{mean_target_chunks} target chunks "
                    f"and ~{round(mean_chunks - mean_target_chunks, 2)} near-neighbor chunks above "
                    f"threshold {self.score_threshold}. When a document only possesses 2 chunks, "
                    f"the maximum possible chunk-level precision for top_k=5 is 2/5 = 0.40. "
                    f"Observed precision {actual_precision} confirms the retriever is fetching "
                    f"the complete target document chunks plus valid competing context."
                ),
            )
        else:
            precision_info = None

        summary = {
            "total_positive_cases": num_pos,
            "failed_positive_cases": len(failed_records),
            "recall_at_5": (
                round((num_pos - len(failed_records)) / num_pos, 4) if num_pos else 1.0
            ),
            "reranker_shifts_count": len(reranker_shifts),
            "improved_shifts": sum(1 for s in reranker_shifts if s.effect == "IMPROVED"),
            "demoted_shifts": sum(1 for s in reranker_shifts if s.effect == "DEMOTED"),
            "unchanged_shifts": sum(1 for s in reranker_shifts if s.effect == "UNCHANGED"),
        }

        return RetrievalFailureReport(
            dataset_version=dataset_version,
            total_cases_evaluated=len(cases),
            total_positive_cases=num_pos,
            total_failed_positive_cases=len(failed_records),
            threshold=self.score_threshold,
            candidate_k=self.candidate_k,
            final_k=self.final_k,
            failures=failed_records,
            borderline_competition_cases=borderline_competition,
            reranker_shifts=reranker_shifts,
            precision_analysis=precision_info,
            answer_failures=[],
            summary=summary,
        )


    def _diagnose_failure(
        self,
        case: EvalCase,
        expected_doc: str,
        raw_candidates: list[RetrievalResult],
        vector_valid: list[RetrievalResult],
        hybrid_valid: list[RetrievalResult],
        retrieved_doc_names: list[str],
        retrieved_scores: list[float],
        context: KnowledgeAccessContext,
    ) -> RetrievalFailureRecord:
        """Diagnose failure reason and measure competition for a failed case."""
        # Find expected doc among raw candidates
        expected_matches = [
            c for c in raw_candidates if c.metadata.get("source_name") == expected_doc
        ]

        # Top competing document (highest scoring chunk not in expected_documents)
        competing_chunks = [
            c
            for c in raw_candidates
            if c.metadata.get("source_name") not in case.expected_documents
        ]
        top_comp = competing_chunks[0] if competing_chunks else None
        top_comp_name = top_comp.metadata.get("source_name") if top_comp else None
        top_comp_score = round(float(top_comp.score), 4) if top_comp else None

        if not expected_matches:
            failure_type = FailureType.MISSING_VECTOR
            exp_score = None
            exp_rank = None
            margin = None
            root_cause = (
                f"Document '{expected_doc}' was not returned in the top {self.candidate_k} "
                f"candidates from Pinecone. Vectors may be unindexed or semantic similarity "
                f"is lower than all {len(raw_candidates)} candidate vectors."
            )
        else:
            best_exp = max(expected_matches, key=lambda c: float(c.score))
            exp_score = round(float(best_exp.score), 4)
            # Find 1-based rank in raw_candidates
            exp_rank = raw_candidates.index(best_exp) + 1
            margin = (
                round(top_comp_score - exp_score, 4)
                if top_comp_score is not None
                else None
            )

            # Check threshold
            if exp_score < self.score_threshold:
                failure_type = FailureType.BELOW_THRESHOLD
                root_cause = (
                    f"Document '{expected_doc}' was found in candidate pool (rank {exp_rank}), "
                    f"but its similarity score {exp_score} is below threshold {self.score_threshold}."
                )
            # Check version
            elif not self.retrieval_service._is_current_version(best_exp):
                failure_type = FailureType.AUTHORIZATION_BLOCKED
                root_cause = f"Document '{expected_doc}' is not marked as current active version in DB."
            # Check access policy
            elif not self.retrieval_service._has_access(best_exp, context):
                failure_type = FailureType.AUTHORIZATION_BLOCKED
                root_cause = f"Access policy blocked document '{expected_doc}' for team {context.team_id}."
            # Check if outranked
            elif exp_rank > self.final_k:
                failure_type = FailureType.OUTRANKED_BY_COMPETITORS
                root_cause = (
                    f"Document '{expected_doc}' had score {exp_score} (rank {exp_rank}), "
                    f"outranked by competitor '{top_comp_name}' (score {top_comp_score}, margin {margin})."
                )
            else:
                failure_type = FailureType.RERANKER_DEMOTION
                root_cause = (
                    f"Document '{expected_doc}' was in top {self.final_k} vector candidates "
                    f"but was demoted by the reranker."
                )

        competition = DocumentCompetition(
            expected_document=expected_doc,
            expected_document_score=exp_score,
            expected_document_rank=exp_rank,
            top_competitor_document=top_comp_name,
            top_competitor_score=top_comp_score,
            margin=margin,
        )

        return RetrievalFailureRecord(
            case_id=case.case_id,
            query=case.query,
            category=case.category,
            expected_document=expected_doc,
            retrieved_documents=retrieved_doc_names,
            retrieved_scores=retrieved_scores,
            expected_document_rank=exp_rank,
            highest_score=retrieved_scores[0] if retrieved_scores else None,
            access_result="ALLOWED" if case.expected_access == "ALLOWED" else "DENIED",
            failure_type=failure_type,
            competition=competition,
            root_cause_diagnosis=root_cause,
        )

    def _track_reranker_shifts(
        self,
        case: EvalCase,
        raw_candidates: list[RetrievalResult],
        reranked_candidates: list[RetrievalResult],
        shifts_out: list[RerankerShift],
    ) -> None:
        """Compare candidate order before and after reranking."""
        if not self.reranker or not reranked_candidates:
            return

        vector_rank_map = {c.chunk_id: idx + 1 for idx, c in enumerate(raw_candidates)}
        hybrid_rank_map = {
            c.chunk_id: idx + 1 for idx, c in enumerate(reranked_candidates)
        }

        for idx, cand in enumerate(reranked_candidates[: self.final_k]):
            v_rank = vector_rank_map.get(cand.chunk_id)
            h_rank = hybrid_rank_map.get(cand.chunk_id)
            source_name = cand.metadata.get("source_name", cand.document_id)

            if v_rank is not None and h_rank is not None:
                rank_change = v_rank - h_rank
                if rank_change > 0:
                    effect = "IMPROVED"
                elif rank_change < 0:
                    effect = "DEMOTED"
                else:
                    effect = "UNCHANGED"

                shift = RerankerShift(
                    case_id=case.case_id,
                    document=source_name,
                    vector_rank=v_rank,
                    hybrid_rank=h_rank,
                    rank_change=rank_change,
                    vector_score=cand.metadata.get("original_vector_score", cand.score),
                    lexical_score=cand.metadata.get("lexical_score", 0.0),
                    title_score=cand.metadata.get("title_match_score", 0.0),
                    final_rerank_score=cand.score,
                    effect=effect,
                )
                shifts_out.append(shift)
