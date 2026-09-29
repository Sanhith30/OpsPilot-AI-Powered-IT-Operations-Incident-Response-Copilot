from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.knowledge_document_version import (
    KnowledgeDocumentVersion,
)


class KnowledgeDocumentVersionRepository:

    def __init__(self, db: Session) -> None:
        self.db = db

    def add(
        self,
        version: KnowledgeDocumentVersion,
    ) -> KnowledgeDocumentVersion:
        self.db.add(version)
        return version

    def get_by_id(
        self,
        version_id: int,
    ) -> KnowledgeDocumentVersion | None:
        return self.db.scalar(
            select(KnowledgeDocumentVersion).where(
                KnowledgeDocumentVersion.version_id == version_id
            )
        )

    def get_versions(
        self,
        document_id: int,
    ) -> list[KnowledgeDocumentVersion]:
        return list(
            self.db.scalars(
                select(KnowledgeDocumentVersion)
                .where(
                    KnowledgeDocumentVersion.document_id == document_id
                )
                .order_by(
                    KnowledgeDocumentVersion.version_number
                    .desc()
                )
            )
        )

    def get_latest(
        self,
        document_id: int,
    ) -> KnowledgeDocumentVersion | None:
        return self.db.scalar(
            select(
                KnowledgeDocumentVersion
            )
            .where(
                KnowledgeDocumentVersion.document_id == document_id
            )
            .order_by(
                KnowledgeDocumentVersion.version_number
                .desc()
            )
            .limit(1)
        )
