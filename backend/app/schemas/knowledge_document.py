from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class KnowledgeDocumentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_type: str = Field(min_length=1, max_length=100)
    source_name: str = Field(min_length=1, max_length=500)
    title: str = Field(min_length=1, max_length=500)
    description: str | None = None
    owner_team_id: int | None = None


class KnowledgeDocumentIngestRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str = Field(min_length=1)


class KnowledgeDocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    document_id: int
    source_type: str
    source_name: str
    title: str
    description: str | None = None
    owner_team_id: int | None = None
    status: str
    current_version_id: int | None = None
    created_at: datetime
    updated_at: datetime


class KnowledgeDocumentVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    version_id: int
    document_id: int
    version_number: int
    content_hash: str
    chunk_count: int
    embedding_model: str | None = None
    embedding_dimensions: int | None = None
    ingestion_status: str
    ingestion_error: str | None = None
    created_at: datetime


class KnowledgeIngestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: str
    document_id: int
    version_id: int
    version_number: int
    chunk_count: int
