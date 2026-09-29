from app.ai.rag.access.policy import (
    KnowledgeAccessPolicy,
)
from app.ai.rag.retrieval.service import (
    KnowledgeRetrievalService,
)
from app.ai.rag.reranking.base import Reranker
from app.ai.rag.vectorstore.factory import (
    create_vector_store,
)


def create_knowledge_retrieval_service(
    *,
    document_repository,
    reranker: Reranker | None = None,
) -> KnowledgeRetrievalService:
    return KnowledgeRetrievalService(
        vector_store=create_vector_store(),
        document_repository=document_repository,
        access_policy=KnowledgeAccessPolicy(),
        reranker=reranker,
    )
