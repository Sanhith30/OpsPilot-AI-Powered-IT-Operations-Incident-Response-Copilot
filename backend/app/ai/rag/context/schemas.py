from typing import Any

from pydantic import BaseModel, Field


class RAGContextItem(BaseModel):
    citation_id: str

    chunk_id: str
    document_id: str

    source_type: str
    source_name: str
    title: str

    version_number: int

    score: float = Field(
        ge=0.0,
        le=1.0,
    )

    content: str

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )


class RAGContext(BaseModel):
    query: str

    items: list[RAGContextItem] = Field(
        default_factory=list
    )

    formatted_context: str

    item_count: int

    has_context: bool

    def get_by_citation(
        self,
        citation_id: str,
    ) -> RAGContextItem | None:
        for item in self.items:
            if item.citation_id == citation_id:
                return item

        return None
