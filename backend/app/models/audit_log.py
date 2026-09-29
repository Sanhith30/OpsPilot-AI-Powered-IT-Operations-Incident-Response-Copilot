from __future__ import annotations

from datetime import datetime
from ipaddress import IPv4Address, IPv6Address
from typing import Any

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    audit_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    actor_user_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey(
            "core.users.user_id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    actor_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    resource_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    resource_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    incident_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey(
            "core.incidents.incident_id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    investigation_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey(
            "core.investigations.investigation_id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    ticket_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey(
            "core.tickets.ticket_id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    action_result: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    request_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    ip_address: Mapped[IPv4Address | IPv6Address | None] = (
        mapped_column(
            INET,
            nullable=True,
        )
    )

    user_agent: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    details: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped["User | None"] = relationship(
        "User",
        back_populates="audit_logs",
    )