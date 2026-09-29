from fastapi import APIRouter, Depends

from app.api.dependencies import (
    get_knowledge_document_service,
    require_permission,
)
from app.schemas.knowledge_document import (
    KnowledgeDocumentCreate,
    KnowledgeDocumentIngestRequest,
    KnowledgeDocumentResponse,
    KnowledgeDocumentVersionResponse,
    KnowledgeIngestionResponse,
)
from app.services.knowledge_document_service import (
    KnowledgeDocumentService,
)

router = APIRouter(
    prefix="/knowledge/documents",
    tags=["Knowledge Documents"],
)


@router.get(
    "",
    response_model=list[KnowledgeDocumentResponse],
)
def get_documents(
    current_user=Depends(require_permission("RUNBOOK_SEARCH")),
    service: KnowledgeDocumentService = Depends(
        get_knowledge_document_service
    ),
):
    return service.get_all_documents()


@router.get(
    "/{document_id}",
    response_model=KnowledgeDocumentResponse,
)
def get_document(
    document_id: int,
    current_user=Depends(require_permission("RUNBOOK_SEARCH")),
    service: KnowledgeDocumentService = Depends(
        get_knowledge_document_service
    ),
):
    return service.get_document_by_id(document_id)


@router.get(
    "/{document_id}/versions",
    response_model=list[KnowledgeDocumentVersionResponse],
)
def get_document_versions(
    document_id: int,
    current_user=Depends(require_permission("RUNBOOK_SEARCH")),
    service: KnowledgeDocumentService = Depends(
        get_knowledge_document_service
    ),
):
    return service.get_document_versions(document_id)


@router.post(
    "",
    response_model=KnowledgeDocumentResponse,
)
def create_document(
    request: KnowledgeDocumentCreate,
    current_user=Depends(require_permission("ROLE_MANAGE")),
    service: KnowledgeDocumentService = Depends(
        get_knowledge_document_service
    ),
):
    return service.create_document(
        data=request,
        actor_user_id=current_user.user_id,
    )


@router.post(
    "/{document_id}/ingest",
    response_model=KnowledgeIngestionResponse,
)
def ingest_document_content(
    document_id: int,
    request: KnowledgeDocumentIngestRequest,
    current_user=Depends(require_permission("ROLE_MANAGE")),
    service: KnowledgeDocumentService = Depends(
        get_knowledge_document_service
    ),
):
    return service.ingest_document(
        document_id=document_id,
        content=request.content,
        actor_user_id=current_user.user_id,
    )


@router.post(
    "/{document_id}/archive",
    response_model=KnowledgeDocumentResponse,
)
def archive_document(
    document_id: int,
    current_user=Depends(require_permission("ROLE_MANAGE")),
    service: KnowledgeDocumentService = Depends(
        get_knowledge_document_service
    ),
):
    return service.archive_document(
        document_id=document_id,
        actor_user_id=current_user.user_id,
    )
