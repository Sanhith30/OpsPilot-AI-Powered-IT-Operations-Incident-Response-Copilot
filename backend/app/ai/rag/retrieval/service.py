from typing import Any

from app.ai.rag.access.policy import (
    KnowledgeAccessContext,
    KnowledgeAccessPolicy,
)
from app.ai.rag.retrieval.schemas import (
    RetrievalFilters,
    RetrievalQuery,
    RetrievalResponse,
)
from app.ai.rag.schemas import RetrievalResult
from app.ai.rag.vectorstore.base import VectorStore
from app.observability.metrics import (
    RAG_RETRIEVAL_RESULTS_TOTAL,
    RAG_RETRIEVALS_TOTAL,
)
from app.observability.tracing import get_tracer
from app.repositories.knowledge_document_repository import (
    KnowledgeDocumentRepository,
)

from app.ai.rag.reranking.base import Reranker

tracer = get_tracer("opspilot.rag.retrieval")


class KnowledgeRetrievalService:

    def __init__(
        self,
        *,
        vector_store: VectorStore,
        document_repository: KnowledgeDocumentRepository,
        access_policy: KnowledgeAccessPolicy,
        reranker: Reranker | None = None,
    ) -> None:
        self.vector_store = vector_store
        self.document_repository = document_repository
        self.access_policy = access_policy
        self.reranker = reranker

    def _build_metadata_filter(
        self,
        filters: RetrievalFilters,
    ) -> dict[str, Any]:
        metadata_filter: dict[str, Any] = {}

        if filters.source_type:
            metadata_filter["source_type"] = filters.source_type

        if filters.source_name:
            metadata_filter["source_name"] = filters.source_name

        if filters.document_id:
            metadata_filter["document_id"] = filters.document_id

        if filters.version_number is not None:
            metadata_filter["version_number"] = filters.version_number

        return metadata_filter

    def _is_current_version(
        self,
        result: RetrievalResult,
    ) -> bool:
        source_type = result.metadata.get("source_type")
        source_name = result.metadata.get("source_name")
        version_number = result.metadata.get("version_number")

        if not source_type or not source_name:
            return False

        if version_number is None:
            return False

        access_record = self.document_repository.get_access_record(
            source_type=source_type,
            source_name=source_name,
        )

        if access_record is None:
            return False

        document, current_version = access_record

        if document.status != "ACTIVE":
            return False

        if current_version is None:
            return False

        return current_version.version_number == int(version_number)

    def _has_access(
        self,
        result: RetrievalResult,
        context: KnowledgeAccessContext,
    ) -> bool:
        source_type = result.metadata.get("source_type")
        source_name = result.metadata.get("source_name")

        if not source_type or not source_name:
            return False

        access_record = self.document_repository.get_access_record(
            source_type=source_type,
            source_name=source_name,
        )

        if access_record is None:
            return False

        document, _ = access_record

        return self.access_policy.can_access(
            owner_team_id=document.owner_team_id,
            context=context,
        )

    def retrieve(
        self,
        request: RetrievalQuery,
        *,
        context: KnowledgeAccessContext,
    ) -> RetrievalResponse:
        query = request.query.strip()

        if not query:
            raise ValueError(
                "Retrieval query cannot be empty"
            )

        metadata_filter = self._build_metadata_filter(
            request.filters
        )

        candidate_k = min(
            max(request.top_k * 3, request.top_k),
            50,
        )

        with tracer.start_as_current_span(
            "rag.retrieve"
        ) as span:
            span.set_attribute(
                "opspilot.rag.top_k",
                request.top_k,
            )

            try:
                if self.reranker is not None:
                    # 1. Pinecone candidate retrieval: Top candidate_k candidates
                    raw_results: list[RetrievalResult] = self.vector_store.search(
                        query,
                        top_k=candidate_k,
                        score_threshold=None,
                        metadata_filter=(
                            metadata_filter if metadata_filter else None
                        ),
                    )

                    # 2. Reranker: score and rank candidates
                    ranked_candidates: list[RetrievalResult] = self.reranker.rerank(
                        query=query,
                        candidates=raw_results,
                        top_k=candidate_k,
                    )
                else:
                    raw_results = self.vector_store.search(
                        query,
                        top_k=candidate_k,
                        score_threshold=request.score_threshold,
                        metadata_filter=(
                            metadata_filter if metadata_filter else None
                        ),
                    )
                    ranked_candidates = raw_results

                valid_results: list[RetrievalResult] = []

                for result in ranked_candidates:
                    # 3. Relevance gate against score_threshold
                    relevance_score = result.metadata.get(
                        "original_vector_score", result.score
                    )
                    if (
                        request.score_threshold is not None
                        and (
                            result.score < request.score_threshold
                            or relevance_score < request.score_threshold
                        )
                    ):
                        continue

                    # 4. Current-version check
                    if not self._is_current_version(result):
                        continue

                    # 5. Authorization check
                    if not self._has_access(result, context):
                        continue

                    valid_results.append(result)

                    if len(valid_results) >= request.top_k:
                        break

                RAG_RETRIEVALS_TOTAL.labels(status="SUCCESS").inc()
                RAG_RETRIEVAL_RESULTS_TOTAL.inc(len(valid_results))

                span.set_attribute(
                    "opspilot.rag.result_count",
                    len(valid_results),
                )
                span.set_attribute(
                    "opspilot.rag.status",
                    "SUCCESS",
                )

                return RetrievalResponse(
                    query=query,
                    results=valid_results,
                    result_count=len(valid_results),
                    applied_filters=request.filters,
                )

            except Exception:
                RAG_RETRIEVALS_TOTAL.labels(status="FAILURE").inc()
                span.set_attribute(
                    "opspilot.rag.status",
                    "FAILURE",
                )
                raise

    def retrieve_text(
        self,
        query: str,
        *,
        context: KnowledgeAccessContext,
        top_k: int = 5,
        score_threshold: float | None = None,
        filters: RetrievalFilters | None = None,
    ) -> list[RetrievalResult]:
        request = RetrievalQuery(
            query=query,
            top_k=top_k,
            score_threshold=score_threshold,
            filters=(
                filters or RetrievalFilters()
            ),
        )

        response = self.retrieve(
            request,
            context=context,
        )

        return list(response.results)
