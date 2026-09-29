from __future__ import annotations
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.chat_message import ChatMessage
    from app.models.incident import Incident
    from app.models.user import User


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    session_id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("core.users.user_id", ondelete="CASCADE"),
        nullable=False,
    )

    incident_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("core.incidents.incident_id", ondelete="SET NULL"),
        nullable=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="New Conversation",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    messages: Mapped[List[ChatMessage]] = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.message_id.asc()",
    )
    user: Mapped[User] = relationship("User")
    incident: Mapped[Optional[Incident]] = relationship("Incident")
