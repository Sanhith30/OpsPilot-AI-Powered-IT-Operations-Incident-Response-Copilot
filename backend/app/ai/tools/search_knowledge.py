from typing import Any

from pydantic import BaseModel, Field

from app.ai.rag.access.policy import KnowledgeAccessContext
from app.ai.rag.retrieval.schemas import RetrievalFilters, RetrievalQuery
from app.ai.rag.retrieval.service import KnowledgeRetrievalService
from app.ai.tools.base import BaseTool


class SearchKnowledgeInput(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    top_k: int = Field(default=5, ge=1, le=20)
    score_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    filters: RetrievalFilters = Field(default_factory=RetrievalFilters)


class SearchKnowledgeTool(BaseTool):
    name = "search_knowledge"
    description = (
        "Search the authorized, current OpsPilot knowledge base "
        "for operational documentation and runbook evidence."
    )

    args_schema = SearchKnowledgeInput
    input_model = SearchKnowledgeInput

    def __init__(
        self,
        *,
        retrieval_service: KnowledgeRetrievalService,
        access_context: KnowledgeAccessContext,
    ) -> None:
        self.retrieval_service = retrieval_service
        self.access_context = access_context

    def execute(self, validated_input: SearchKnowledgeInput) -> dict[str, Any]:
        query_obj = RetrievalQuery(
            query=validated_input.query,
            top_k=validated_input.top_k,
            score_threshold=validated_input.score_threshold,
            filters=validated_input.filters,
        )

        response = self.retrieval_service.retrieve(
            query_obj,
            context=self.access_context,
        )

        return response.model_dump(mode="json")
