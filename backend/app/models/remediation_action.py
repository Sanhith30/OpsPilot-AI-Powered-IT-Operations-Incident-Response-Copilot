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


class RemediationAction(Base):
    __tablename__ = "remediation_actions"

    remediation_id: Mapped[int] = mapped_column(
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

    investigation_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey(
            "core.investigations.investigation_id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    intelligence_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey(
            "core.incident_intelligence.intelligence_id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    action_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    action_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    rationale: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="PENDING_APPROVAL",
    )

    execution_payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    requested_by_user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "core.users.user_id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    approved_by_user_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey(
            "core.users.user_id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    review_comment: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    execution_result: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    execution_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    execution_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    verification_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="PENDING",
    )

    verification_result: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
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

    incident: Mapped["Incident"] = relationship(
        "Incident",
        back_populates="remediations",
    )

    investigation: Mapped["Investigation | None"] = relationship(
        "Investigation",
        back_populates="remediations",
    )

    intelligence: Mapped["IncidentIntelligence | None"] = relationship(
        "IncidentIntelligence",
        back_populates="remediations",
    )

    requested_by: Mapped["User"] = relationship(
        "User",
        foreign_keys=[requested_by_user_id],
    )

    approved_by: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[approved_by_user_id],
    )
