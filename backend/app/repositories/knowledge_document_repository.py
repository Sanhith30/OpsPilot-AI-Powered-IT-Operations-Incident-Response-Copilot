from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.knowledge_document import (
    KnowledgeDocument,
)
from app.models.knowledge_document_version import (
    KnowledgeDocumentVersion,
)


class KnowledgeDocumentRepository:

    def __init__(self, db: Session) -> None:
        self.db = db

    def add(
        self,
        document: KnowledgeDocument,
    ) -> KnowledgeDocument:
        self.db.add(document)
        return document

    def get_by_id(
        self,
        document_id: int,
    ) -> KnowledgeDocument | None:
        return self.db.scalar(
            select(KnowledgeDocument).where(
                KnowledgeDocument.document_id == document_id
            )
        )

    def get_by_source(
        self,
        *,
        source_type: str,
        source_name: str,
    ) -> KnowledgeDocument | None:
        return self.db.scalar(
            select(KnowledgeDocument).where(
                KnowledgeDocument.source_type == source_type,
                KnowledgeDocument.source_name == source_name,
            )
        )

    def get_all(
        self,
    ) -> list[KnowledgeDocument]:
        return list(
            self.db.scalars(
                select(KnowledgeDocument).order_by(
                    KnowledgeDocument.document_id
                )
            ).all()
        )

    def get_all_active(
        self,
    ) -> list[KnowledgeDocument]:
        return list(
            self.db.scalars(
                select(KnowledgeDocument)
                .where(
                    KnowledgeDocument.status == "ACTIVE"
                )
                .order_by(
                    KnowledgeDocument.title
                )
            )
        )

    def get_current_version(
        self,
        document_id: int,
    ) -> KnowledgeDocumentVersion | None:
        document = self.get_by_id(document_id)
        if document is None or document.current_version_id is None:
            return None

        return self.db.scalar(
            select(KnowledgeDocumentVersion).where(
                KnowledgeDocumentVersion.version_id
                == document.current_version_id
            )
        )

    def get_access_record(
        self,
        *,
        source_type: str,
        source_name: str,
    ) -> tuple[KnowledgeDocument, KnowledgeDocumentVersion | None] | None:
        document = self.get_by_source(
            source_type=source_type,
            source_name=source_name,
        )
        if document is None:
            return None

        current_version = self.get_current_version(
            document.document_id
        )
        return document, current_version
