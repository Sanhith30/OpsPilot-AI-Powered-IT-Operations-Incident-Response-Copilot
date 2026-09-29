from __future__ import annotations

import pytest

from app.ai.rag.evaluation.document_metrics import (
    AggregatedDocument,
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
from app.ai.rag.schemas import RetrievalResult


def test_1_duplicate_chunks_collapse_to_one_document():
    # 5 chunks where 3 belong to Payment API and 2 belong to PostgreSQL
    chunks = [
        RetrievalResult(
            chunk_id="c-1",
            document_id="doc-payment",
            content="Payment chunk 1",
            score=0.82,
            metadata={"source_name": "payment-api-database-timeouts.md", "title": "Payment Runbook"},
        ),
        RetrievalResult(
            chunk_id="c-2",
            document_id="doc-payment",
            content="Payment chunk 2",
            score=0.86,  # Higher score
            metadata={"source_name": "payment-api-database-timeouts.md", "title": "Payment Runbook"},
        ),
        RetrievalResult(
            chunk_id="c-3",
            document_id="doc-pg",
            content="Postgres chunk 1",
            score=0.75,
            metadata={"source_name": "postgresql-connection-pool-guide.md", "title": "PG Guide"},
        ),
        RetrievalResult(
            chunk_id="c-4",
            document_id="doc-payment",
            content="Payment chunk 3",
            score=0.79,
            metadata={"source_name": "payment-api-database-timeouts.md", "title": "Payment Runbook"},
        ),
        RetrievalResult(
            chunk_id="c-5",
            document_id="doc-pg",
            content="Postgres chunk 2",
            score=0.74,
            metadata={"source_name": "postgresql-connection-pool-guide.md", "title": "PG Guide"},
        ),
    ]

    docs = unique_documents(chunks)
    assert len(docs) == 2

    # Preserves first appearance order (document_rank)
    doc_1 = docs[0]
    assert doc_1.source_name == "payment-api-database-timeouts.md"
    assert doc_1.document_rank == 1
    assert doc_1.best_chunk_rank == 1
    assert doc_1.best_score == 0.86  # Highest score retained
    assert doc_1.chunk_count == 3

    doc_2 = docs[1]
    assert doc_2.source_name == "postgresql-connection-pool-guide.md"
    assert doc_2.document_rank == 2
    assert doc_2.best_chunk_rank == 3
    assert doc_2.best_score == 0.75
    assert doc_2.chunk_count == 2


def test_2_correct_document_at_rank_1():
    expected = ["payment-api-database-timeouts.md"]
    retrieved_chunks = [
        "payment-api-database-timeouts.md",
        "payment-api-database-timeouts.md",
        "postgresql-connection-pool-guide.md",
        "redis-cache-failures.md",
        "deployment-rollback-sop.md",
    ]
    docs = unique_documents(retrieved_chunks)

    recall = calculate_document_recall_at_k(expected, docs)
    precision = calculate_document_precision_at_k(expected, docs)
    rr = calculate_document_reciprocal_rank(expected, docs)

    assert recall == 1.0
    assert precision == round(1 / 4, 4)  # 1 relevant of 4 unique documents
    assert rr == 1.0  # 1 / 1

    diag = extract_document_diagnostics(expected, docs, retrieved_chunks)
    assert diag.expected_document_rank == 1
    assert diag.best_chunk_rank == 1
    assert diag.unique_document_count == 4
    assert diag.target_document_present is True


def test_3_correct_document_at_rank_5():
    expected = ["target-doc.md"]
    retrieved_chunks = [
        "comp-1.md",
        "comp-2.md",
        "comp-3.md",
        "comp-4.md",
        "target-doc.md",
    ]
    docs = unique_documents(retrieved_chunks)

    diag = extract_document_diagnostics(expected, docs, retrieved_chunks)
    assert diag.expected_document_rank == 5
    assert diag.best_chunk_rank == 5
    assert diag.target_document_present is True

    # At k=5: target doc is included
    assert calculate_document_recall_at_k(expected, docs, k=5) == 1.0
    assert calculate_document_reciprocal_rank(expected, docs) == 0.2

    # At k=4: target doc is cut off
    assert calculate_document_recall_at_k(expected, docs, k=4) == 0.0


def test_4_correct_document_absent():
    expected = ["expected-secret.md"]
    retrieved_chunks = [
        "public-1.md",
        "public-2.md",
        "public-3.md",
    ]
    docs = unique_documents(retrieved_chunks)

    diag = extract_document_diagnostics(expected, docs, retrieved_chunks)
    assert diag.expected_document_rank is None
    assert diag.best_chunk_rank is None
    assert diag.unique_document_count == 3
    assert diag.target_document_present is False

    assert calculate_document_recall_at_k(expected, docs) == 0.0
    assert calculate_document_precision_at_k(expected, docs) == 0.0
    assert calculate_document_reciprocal_rank(expected, docs) == 0.0


def test_5_multiple_chunks_from_same_document():
    expected = ["order-service-latency.md"]
    retrieved_chunks = [
        "order-service-latency.md",
        "order-service-latency.md",
        "order-service-latency.md",
        "order-service-latency.md",
        "order-service-latency.md",
    ]
    docs = unique_documents(retrieved_chunks)

    assert len(docs) == 1
    assert docs[0].chunk_count == 5

    # Chunk precision = 5/5 = 1.0, Document precision = 1/1 = 1.0
    assert calculate_chunk_precision_at_k(expected, retrieved_chunks) == 1.0
    assert calculate_document_precision_at_k(expected, docs) == 1.0
    assert calculate_document_recall_at_k(expected, docs) == 1.0


def test_6_multiple_relevant_documents():
    expected = ["doc-a.md", "doc-b.md"]
    retrieved_chunks = [
        "doc-a.md",
        "doc-c.md",
        "doc-b.md",
        "doc-d.md",
    ]
    docs = unique_documents(retrieved_chunks)

    recall = calculate_document_recall_at_k(expected, docs)
    precision = calculate_document_precision_at_k(expected, docs)
    rr = calculate_document_reciprocal_rank(expected, docs)

    assert recall == 1.0  # Both doc-a and doc-b found
    assert precision == 2 / 4  # 2 relevant of 4 unique
    assert rr == 1.0  # First relevant doc is rank 1


def test_7_empty_results():
    expected = ["payment-api.md"]
    docs = unique_documents([])
    assert docs == []

    assert calculate_document_recall_at_k(expected, docs) == 0.0
    assert calculate_document_precision_at_k(expected, docs) == 0.0
    assert calculate_document_reciprocal_rank(expected, docs) == 0.0
    assert calculate_chunk_recall_at_k(expected, []) == 0.0
    assert calculate_chunk_precision_at_k(expected, []) == 0.0

    diag = extract_document_diagnostics(expected, docs, [])
    assert diag.expected_document_rank is None
    assert diag.best_chunk_rank is None
    assert diag.unique_document_count == 0
    assert diag.target_document_present is False


def test_8_mrr_calculation():
    # Case 1: rank 1 (1.0), Case 2: rank 2 (0.5), Case 3: rank 4 (0.25), Case 4: absent (0.0)
    rrs = [1.0, 0.5, 0.25, 0.0]
    expected_mrr = round((1.0 + 0.5 + 0.25 + 0.0) / 4, 4)  # 0.4375
    assert calculate_document_mrr(rrs) == expected_mrr
    assert calculate_document_mrr([]) == 0.0


def test_9_document_precision_vs_chunk_precision():
    """
    Demonstrates the Step 17.20 / 17.21 finding:
    Corpus with 2 chunks per doc causes chunk precision ~0.40,
    while document precision properly measures unique document relevance.
    """
    expected = ["payment-api-database-timeouts.md"]
    retrieved_chunks = [
        "payment-api-database-timeouts.md",  # target chunk 1
        "payment-api-database-timeouts.md",  # target chunk 2
        "postgresql-connection-pool-guide.md",  # competitor chunk 1
        "redis-cache-failures.md",  # competitor chunk 2
        "postgresql-connection-pool-guide.md",  # competitor chunk 3
    ]

    docs = unique_documents(retrieved_chunks)
    assert len(docs) == 3  # payment, postgres, redis

    chunk_prec = calculate_chunk_precision_at_k(expected, retrieved_chunks)
    doc_prec = calculate_document_precision_at_k(expected, docs)

    # Chunk precision = 2/5 = 0.40
    assert chunk_prec == 0.40

    # Document precision = 1 target doc / 3 unique docs = 0.3333
    assert doc_prec == round(1 / 3, 4)

    # Document Recall and MRR are perfect
    assert calculate_document_recall_at_k(expected, docs) == 1.0
    assert calculate_document_reciprocal_rank(expected, docs) == 1.0


def test_10_regression_against_17_20_failures():
    """
    Regression check against the RAG-026 and RAG-037 failure scenario:
    Unindexed target document yields 0 chunks and 0 recall.
    Indexed target document yields rank 1 and 1.0 recall.
    """
    expected = ["runbooks/authentication-service-token-errors.md"]

    # 1. Failure state (unindexed document due to vector deletion bug)
    failed_chunks = [
        "payment-api-database-timeouts.md",
        "runbooks/order-service-latency.md",
    ]
    failed_docs = unique_documents(failed_chunks)
    failed_diag = extract_document_diagnostics(expected, failed_docs, failed_chunks)

    assert failed_diag.target_document_present is False
    assert failed_diag.expected_document_rank is None
    assert calculate_document_recall_at_k(expected, failed_docs) == 0.0

    # 2. Resolved state (re-indexed with 2 chunks at rank 1 and 2)
    resolved_chunks = [
        "runbooks/authentication-service-token-errors.md",
        "runbooks/authentication-service-token-errors.md",
        "payment-api-database-timeouts.md",
        "postmortems/payment-api-2026-09-timeout.md",
    ]
    resolved_docs = unique_documents(resolved_chunks)
    resolved_diag = extract_document_diagnostics(expected, resolved_docs, resolved_chunks)

    assert resolved_diag.target_document_present is True
    assert resolved_diag.expected_document_rank == 1
    assert resolved_diag.best_chunk_rank == 1
    assert calculate_document_recall_at_k(expected, resolved_docs) == 1.0
    assert calculate_document_reciprocal_rank(expected, resolved_docs) == 1.0
