from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class IncidentEvent(Base):
    __tablename__ = "incident_events"

    incident_event_id: Mapped[int] = mapped_column(
        "event_id",
        BigInteger,
        primary_key=True,
    )

    incident_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "core.incidents.incident_id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        "event_message",
        Text,
        nullable=False,
    )

    event_time: Mapped[datetime] = mapped_column(
        "event_timestamp",
        DateTime(timezone=True),
        nullable=False,
    )

    created_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey(
            "core.users.user_id",
            ondelete="SET NULL",
        ),
    )

    event_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata",
        JSONB,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    incident: Mapped["Incident"] = relationship(
        back_populates="events"
    )

    created_by_user: Mapped["User | None"] = relationship(
        back_populates="incident_events_created"
    )