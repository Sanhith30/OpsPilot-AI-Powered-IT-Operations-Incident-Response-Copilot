from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.knowledge_document_version import (
        KnowledgeDocumentVersion,
    )
    from app.models.team import Team


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"
    __table_args__ = {
        "schema": "core",
    }

    document_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )
    source_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    source_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
    )
    owner_team_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "core.teams.team_id",
            ondelete="SET NULL",
        ),
    )
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="ACTIVE",
    )
    current_version_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "core.knowledge_document_versions.version_id",
            ondelete="SET NULL",
        ),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    owner_team: Mapped["Team | None"] = relationship(
        foreign_keys=[owner_team_id],
    )
    versions: Mapped[
        list["KnowledgeDocumentVersion"]
    ] = relationship(
        foreign_keys="KnowledgeDocumentVersion.document_id",
        back_populates="document",
    )
