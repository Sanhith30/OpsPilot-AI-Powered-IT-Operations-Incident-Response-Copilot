from __future__ import annotations
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.chat_session import ChatSession
    from app.models.investigation import Investigation


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    message_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    session_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("core.chat_sessions.session_id", ondelete="CASCADE"),
        nullable=False,
    )

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    tool_trace: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    citations: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    risk: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
    )

    investigation_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("core.investigations.investigation_id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    session: Mapped[ChatSession] = relationship(
        "ChatSession",
        back_populates="messages",
    )
    investigation: Mapped[Optional[Investigation]] = relationship("Investigation")
