from sqlalchemy.orm import Session

from app.ai.rag.ingestion.service import KnowledgeIngestionService
from app.core.exceptions import (
    ConflictError,
    NotFoundError,
    ValidationError,
)
from app.models.knowledge_document import KnowledgeDocument
from app.models.knowledge_document_version import KnowledgeDocumentVersion
from app.repositories.knowledge_document_repository import (
    KnowledgeDocumentRepository,
)
from app.repositories.knowledge_document_version_repository import (
    KnowledgeDocumentVersionRepository,
)
from app.schemas.knowledge_document import KnowledgeDocumentCreate
from app.services.audit_log_service import AuditLogService


class KnowledgeDocumentService:

    def __init__(
        self,
        db: Session,
        document_repository: KnowledgeDocumentRepository,
        version_repository: KnowledgeDocumentVersionRepository,
        ingestion_service: KnowledgeIngestionService,
        audit_log_service: AuditLogService,
    ) -> None:
        self.db = db
        self.document_repository = document_repository
        self.version_repository = version_repository
        self.ingestion_service = ingestion_service
        self.audit_log_service = audit_log_service

    def get_all_documents(self) -> list[KnowledgeDocument]:
        return self.document_repository.get_all()

    def get_document_by_id(self, document_id: int) -> KnowledgeDocument:
        doc = self.document_repository.get_by_id(document_id)
        if doc is None:
            raise NotFoundError("Knowledge document not found.")
        return doc

    def get_document_versions(
        self, document_id: int
    ) -> list[KnowledgeDocumentVersion]:
        self.get_document_by_id(document_id)
        return self.version_repository.get_versions(document_id)

    def create_document(
        self,
        data: KnowledgeDocumentCreate,
        actor_user_id: int | None = None,
    ) -> KnowledgeDocument:
        existing = self.document_repository.get_by_source(
            source_type=data.source_type,
            source_name=data.source_name,
        )
        if existing is not None:
            raise ConflictError(
                "Knowledge document with this source already exists."
            )

        document = KnowledgeDocument(
            source_type=data.source_type,
            source_name=data.source_name,
            title=data.title,
            description=data.description,
            owner_team_id=data.owner_team_id,
            status="ACTIVE",
        )
        self.document_repository.add(document)
        self.db.flush()

        self.audit_log_service.add_to_transaction(
            action="KNOWLEDGE_DOCUMENT_CREATED",
            user_id=actor_user_id,
            resource_type="KNOWLEDGE_DOCUMENT",
            resource_id=document.document_id,
            details={
                "document_id": document.document_id,
                "source_type": document.source_type,
                "source_name": document.source_name,
                "title": document.title,
            },
            action_result="SUCCESS",
        )
        self.db.commit()
        self.db.refresh(document)
        return document

    def ingest_document(
        self,
        document_id: int,
        content: str,
        actor_user_id: int | None = None,
    ) -> dict:
        document = self.get_document_by_id(document_id)
        if document.status != "ACTIVE":
            raise ValidationError(
                f"Cannot ingest into knowledge document with status '{document.status}'."
            )

        try:
            result = self.ingestion_service.ingest_content(
                document_id=document.document_id,
                content=content,
                actor_user_id=actor_user_id,
            )
            self.audit_log_service.add_to_transaction(
                action="KNOWLEDGE_DOCUMENT_INGESTED",
                user_id=actor_user_id,
                resource_type="KNOWLEDGE_DOCUMENT",
                resource_id=document.document_id,
                details={
                    "document_id": document.document_id,
                    "source_name": document.source_name,
                    "version_number": result["version_number"],
                    "ingestion_status": result["status"],
                    "chunk_count": result["chunk_count"],
                },
                action_result="SUCCESS",
            )
            self.db.commit()
            return result
        except Exception as exc:
            try:
                self.audit_log_service.add_to_transaction(
                    action="KNOWLEDGE_DOCUMENT_INGESTED",
                    user_id=actor_user_id,
                    resource_type="KNOWLEDGE_DOCUMENT",
                    resource_id=document.document_id,
                    details={
                        "document_id": document.document_id,
                        "source_name": document.source_name,
                        "error": str(exc),
                    },
                    action_result="FAILURE",
                )
                self.db.commit()
            except Exception:
                pass
            raise

    def archive_document(
        self,
        document_id: int,
        actor_user_id: int | None = None,
    ) -> KnowledgeDocument:
        document = self.get_document_by_id(document_id)
        if document.status == "ARCHIVED":
            return document

        document.status = "ARCHIVED"
        self.audit_log_service.add_to_transaction(
            action="KNOWLEDGE_DOCUMENT_ARCHIVED",
            user_id=actor_user_id,
            resource_type="KNOWLEDGE_DOCUMENT",
            resource_id=document.document_id,
            details={
                "document_id": document.document_id,
                "source_name": document.source_name,
                "status": "ARCHIVED",
            },
            action_result="SUCCESS",
        )
        self.db.commit()
        self.db.refresh(document)
        return document
