from pydantic import BaseModel, Field


class CitationValidationResult(BaseModel):
    valid: bool
    citation_id: str
    reason: str


class FindingValidationResult(BaseModel):
    valid: bool
    invalid_citations: list[str] = Field(default_factory=list)
    validated_citations: list[str] = Field(default_factory=list)
    reason: str | None = None


class GroundingValidationResult(BaseModel):
    valid: bool
    grounding_status: str
    findings_results: list[FindingValidationResult] = Field(default_factory=list)
    invalid_citations: list[str] = Field(default_factory=list)
    validated_citations: list[str] = Field(default_factory=list)
    error_message: str | None = None
