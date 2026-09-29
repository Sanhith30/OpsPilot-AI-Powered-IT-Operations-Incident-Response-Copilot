from __future__ import annotations


def calculate_recall_at_k(expected: list[str], retrieved: list[str]) -> float:
    """Calculate Recall@K for positive queries: fraction of expected documents found."""
    if not expected:
        return 0.0

    retrieved_set = set(retrieved)
    hits = sum(1 for doc in expected if doc in retrieved_set)
    return hits / len(expected)


def calculate_precision_at_k(expected: list[str], retrieved: list[str]) -> float:
    """Calculate Precision@K for positive queries: fraction of retrieved documents that are relevant."""
    if not retrieved or not expected:
        return 0.0

    expected_set = set(expected)
    hits = sum(1 for doc in retrieved if doc in expected_set)
    return hits / len(retrieved)


def calculate_reciprocal_rank(expected: list[str], retrieved: list[str]) -> float:
    """Calculate Reciprocal Rank (1/rank) for the first relevant document found."""
    if not expected or not retrieved:
        return 0.0

    expected_set = set(expected)
    for rank, doc in enumerate(retrieved, start=1):
        if doc in expected_set:
            return 1.0 / rank

    return 0.0


def calculate_mrr(reciprocal_ranks: list[float]) -> float:
    """Calculate Mean Reciprocal Rank (MRR) across a list of reciprocal ranks."""
    if not reciprocal_ranks:
        return 0.0
    return sum(reciprocal_ranks) / len(reciprocal_ranks)


def calculate_unwanted_retrieval_rate(unwanted_flags: list[bool]) -> float:
    """Calculate percentage of negative control queries that unwantedly surfaced documents."""
    if not unwanted_flags:
        return 0.0
    return sum(1 for flag in unwanted_flags if flag) / len(unwanted_flags)


def calculate_authorization_accuracy(passed_flags: list[bool]) -> float:
    """Calculate percentage of authorization checks that passed."""
    if not passed_flags:
        return 1.0
    return sum(1 for p in passed_flags if p) / len(passed_flags)


def calculate_unauthorized_leakage_rate(leakage_flags: list[bool]) -> float:
    """Calculate percentage of unauthorized access attempts that resulted in document leakage."""
    if not leakage_flags:
        return 0.0
    return sum(1 for l in leakage_flags if l) / len(leakage_flags)


def calculate_grounding_rate(valid_citations: int, total_citations: int) -> float:
    """Calculate citation grounding rate: valid citations / total citations."""
    if total_citations <= 0:
        return 1.0
    return min(max(valid_citations / total_citations, 0.0), 1.0)
