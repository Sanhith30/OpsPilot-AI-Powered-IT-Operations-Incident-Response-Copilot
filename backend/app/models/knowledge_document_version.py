from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.knowledge_document import (
        KnowledgeDocument,
    )
    from app.models.user import User


class KnowledgeDocumentVersion(Base):
    __tablename__ = "knowledge_document_versions"
    __table_args__ = {
        "schema": "core",
    }

    version_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )
    document_id: Mapped[int] = mapped_column(
        ForeignKey(
            "core.knowledge_documents.document_id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    version_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    content_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    chunk_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    embedding_model: Mapped[str | None] = mapped_column(
        String(100),
    )
    embedding_dimensions: Mapped[int | None] = mapped_column(
        Integer,
    )
    ingestion_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="PENDING",
    )
    ingestion_error: Mapped[str | None] = mapped_column(
        Text,
    )
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey(
            "core.users.user_id",
            ondelete="SET NULL",
        ),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    document: Mapped[
        "KnowledgeDocument"
    ] = relationship(
        back_populates="versions",
        foreign_keys=[document_id],
    )
    created_by_user: Mapped[
        "User | None"
    ] = relationship(
        foreign_keys=[created_by],
    )
