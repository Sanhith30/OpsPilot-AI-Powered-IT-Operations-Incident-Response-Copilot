from __future__ import annotations

from typing import Any

from app.ai.schemas.evidence import EvidenceItem


def add_evidence(
    evidence: list[dict[str, Any]],
    *,
    source_type: str,
    source_id: str | int,
    timestamp,
    title: str,
    content: str,
    metadata: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    item = EvidenceItem(
        source_type=source_type,
        source_id=str(source_id),
        timestamp=timestamp,
        title=title,
        content=content,
        metadata=metadata or {},
    )

    return [
        *evidence,
        item.model_dump(),
    ]
