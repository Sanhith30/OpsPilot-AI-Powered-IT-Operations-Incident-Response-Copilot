from typing import Any

from pydantic import BaseModel, Field


class KnowledgeDocument(BaseModel):
    document_id: str
    source_type: str
    source_name: str
    title: str
    content: str
    content_hash: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class KnowledgeChunk(BaseModel):
    chunk_id: str
    document_id: str
    content: str
    chunk_index: int = Field(ge=0)
    version_number: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievalResult(BaseModel):
    chunk_id: str
    document_id: str
    content: str
    score: float = Field(ge=0.0)
    metadata: dict[str, Any] = Field(default_factory=dict)
