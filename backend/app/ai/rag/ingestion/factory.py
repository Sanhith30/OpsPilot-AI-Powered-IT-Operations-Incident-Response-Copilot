from app.ai.rag.ingestion.chunker import (
    KnowledgeChunker,
)
from app.ai.rag.ingestion.loader import (
    KnowledgeDocumentLoader,
)
from app.ai.rag.ingestion.normalizer import (
    KnowledgeDocumentNormalizer,
)
from app.ai.rag.ingestion.service import (
    KnowledgeIngestionService,
)
from app.ai.rag.vectorstore.factory import (
    create_vector_store,
)


def create_knowledge_ingestion_service(
    *,
    db,
    document_repository,
    version_repository,
) -> KnowledgeIngestionService:
    return KnowledgeIngestionService(
        loader=KnowledgeDocumentLoader(),
        normalizer=KnowledgeDocumentNormalizer(),
        chunker=KnowledgeChunker(),
        vector_store=create_vector_store(),
        document_repository=document_repository,
        version_repository=version_repository,
        db=db,
    )
