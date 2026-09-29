from __future__ import annotations

from typing import Any, Sequence
from pydantic import BaseModel, Field

from app.ai.rag.schemas import RetrievalResult


class AggregatedDocument(BaseModel):
    document_id: str
    source_name: str
    title: str | None = None
    best_score: float
    best_chunk_rank: int  # 1-indexed position in raw chunk results
    document_rank: int  # 1-indexed position among unique documents
    chunk_count: int = 1


class DocumentRankingDiagnostics(BaseModel):
    expected_document_rank: int | None = None
    best_chunk_rank: int | None = None
    unique_document_count: int = 0
    target_document_present: bool = False


class DocumentRetrievalMetrics(BaseModel):
    count: int = 0
    recall_at_k: float = 0.0
    precision_at_k: float = 0.0
    mrr: float = 0.0


class ChunkRetrievalMetrics(BaseModel):
    count: int = 0
    recall_at_k: float = 0.0
    precision_at_k: float = 0.0
    mrr: float = 0.0


def unique_documents(
    results: Sequence[RetrievalResult | dict[str, Any] | str],
) -> list[AggregatedDocument]:
    """
    Group retrieved chunks by document while retaining the best score and best rank.
    Preserves the order of first appearance (highest score in pre-sorted results).
    """
    if not results:
        return []

    seen: dict[str, AggregatedDocument] = {}
    ordered_docs: list[AggregatedDocument] = []

    for rank, item in enumerate(results, start=1):
        if isinstance(item, RetrievalResult):
            source_name = item.metadata.get("source_name") or item.document_id
            doc_id = item.document_id
            title = item.metadata.get("title")
            score = round(float(item.score), 4)
        elif isinstance(item, dict):
            metadata = item.get("metadata", {})
            source_name = (
                metadata.get("source_name")
                or item.get("source_name")
                or item.get("document_id", f"doc-{rank}")
            )
            doc_id = item.get("document_id") or source_name
            title = metadata.get("title") or item.get("title")
            score = round(float(item.get("score", 0.0)), 4)
        elif isinstance(item, str):
            source_name = item
            doc_id = item
            title = None
            score = 1.0
        else:
            source_name = str(item)
            doc_id = source_name
            title = None
            score = 1.0

        if source_name not in seen:
            doc_entry = AggregatedDocument(
                document_id=doc_id,
                source_name=source_name,
                title=title,
                best_score=score,
                best_chunk_rank=rank,
                document_rank=len(ordered_docs) + 1,
                chunk_count=1,
            )
            seen[source_name] = doc_entry
            ordered_docs.append(doc_entry)
        else:
            existing = seen[source_name]
            existing.chunk_count += 1
            if score > existing.best_score:
                existing.best_score = score

    return ordered_docs


def calculate_document_recall_at_k(
    expected: list[str],
    retrieved_unique_docs: list[str] | list[AggregatedDocument],
    k: int | None = None,
) -> float:
    """Calculate Document-level Recall@K: fraction of expected documents found."""
    if not expected:
        return 0.0

    doc_names = [
        d.source_name if isinstance(d, AggregatedDocument) else str(d)
        for d in retrieved_unique_docs
    ]
    if k is not None and k > 0:
        doc_names = doc_names[:k]

    retrieved_set = set(doc_names)
    hits = sum(1 for doc in expected if doc in retrieved_set)
    return round(hits / len(expected), 4)


def calculate_document_precision_at_k(
    expected: list[str],
    retrieved_unique_docs: list[str] | list[AggregatedDocument],
    k: int | None = None,
) -> float:
    """
    Calculate Document-level Precision@K: fraction of unique retrieved documents
    that are relevant expected documents.
    """
    doc_names = [
        d.source_name if isinstance(d, AggregatedDocument) else str(d)
        for d in retrieved_unique_docs
    ]
    if k is not None and k > 0:
        doc_names = doc_names[:k]

    if not doc_names or not expected:
        return 0.0

    expected_set = set(expected)
    hits = sum(1 for doc in doc_names if doc in expected_set)
    return round(hits / len(doc_names), 4)


def calculate_document_reciprocal_rank(
    expected: list[str],
    retrieved_unique_docs: list[str] | list[AggregatedDocument],
) -> float:
    """Calculate Reciprocal Rank (1/rank) for the first relevant unique document found."""
    if not expected or not retrieved_unique_docs:
        return 0.0

    doc_names = [
        d.source_name if isinstance(d, AggregatedDocument) else str(d)
        for d in retrieved_unique_docs
    ]
    expected_set = set(expected)

    for rank, doc in enumerate(doc_names, start=1):
        if doc in expected_set:
            return round(1.0 / rank, 4)

    return 0.0


def calculate_document_mrr(reciprocal_ranks: list[float]) -> float:
    """Calculate Mean Reciprocal Rank (MRR) for document-level ranking."""
    if not reciprocal_ranks:
        return 0.0
    return round(sum(reciprocal_ranks) / len(reciprocal_ranks), 4)


def calculate_chunk_recall_at_k(
    expected: list[str],
    retrieved_chunks: list[str],
    k: int | None = None,
) -> float:
    """Calculate Chunk-level Recall@K: fraction of expected documents covered by chunks."""
    if not expected:
        return 0.0

    chunks = retrieved_chunks[:k] if (k is not None and k > 0) else retrieved_chunks
    chunk_set = set(chunks)
    hits = sum(1 for doc in expected if doc in chunk_set)
    return round(hits / len(expected), 4)


def calculate_chunk_precision_at_k(
    expected: list[str],
    retrieved_chunks: list[str],
    k: int | None = None,
) -> float:
    """Calculate Chunk-level Precision@K: fraction of retrieved chunks belonging to expected docs."""
    chunks = retrieved_chunks[:k] if (k is not None and k > 0) else retrieved_chunks
    if not chunks or not expected:
        return 0.0

    expected_set = set(expected)
    hits = sum(1 for chunk in chunks if chunk in expected_set)
    return round(hits / len(chunks), 4)


def calculate_chunk_reciprocal_rank(
    expected: list[str],
    retrieved_chunks: list[str],
) -> float:
    """Calculate Chunk-level Reciprocal Rank: 1 / rank of first relevant chunk."""
    if not expected or not retrieved_chunks:
        return 0.0

    expected_set = set(expected)
    for rank, chunk in enumerate(retrieved_chunks, start=1):
        if chunk in expected_set:
            return round(1.0 / rank, 4)

    return 0.0


def extract_document_diagnostics(
    expected_documents: list[str],
    aggregated_docs: list[AggregatedDocument],
    chunk_sources: list[str],
) -> DocumentRankingDiagnostics:
    """
    Extract diagnostic ranking information for an individual query case.
    Distinguishes target document absence from target document presence with
    lower-ranked secondary chunks.
    """
    expected_set = set(expected_documents)

    # 1. Expected document rank among unique documents
    expected_doc_rank = None
    for doc in aggregated_docs:
        if doc.source_name in expected_set:
            expected_doc_rank = doc.document_rank
            break

    # 2. Best chunk rank among raw retrieved chunks
    best_chunk_rank = None
    for rank, chunk_source in enumerate(chunk_sources, start=1):
        if chunk_source in expected_set:
            best_chunk_rank = rank
            break

    unique_doc_count = len(aggregated_docs)
    target_doc_present = expected_doc_rank is not None

    return DocumentRankingDiagnostics(
        expected_document_rank=expected_doc_rank,
        best_chunk_rank=best_chunk_rank,
        unique_document_count=unique_doc_count,
        target_document_present=target_doc_present,
    )
