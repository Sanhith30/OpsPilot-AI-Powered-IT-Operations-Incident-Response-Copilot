from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


ConfidenceLevel = Literal["LOW", "MEDIUM", "HIGH"]


class EvidenceReference(BaseModel):
    source_type: str = Field(
        ...,
        min_length=1,
        max_length=50,
    )

    source_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )


class InvestigationFinding(BaseModel):
    finding: str = Field(
        ...,
        min_length=1,
    )

    confidence: ConfidenceLevel

    evidence_refs: list[EvidenceReference] = Field(
        default_factory=list,
    )


class InvestigationAnalysis(BaseModel):
    summary: str = Field(
        ...,
        min_length=1,
    )

    findings: list[InvestigationFinding] = Field(
        default_factory=list,
    )

    probable_root_cause: str | None = None

    recommendations: list[str] = Field(
        default_factory=list,
    )
