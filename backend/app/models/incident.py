from __future__ import annotations
from datetime import datetime

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


class Incident(Base):
    __tablename__ = "incidents"

    incident_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    incident_number: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    service_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "core.services.service_id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
    )

    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    assigned_team_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "core.teams.team_id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    assigned_user_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey(
            "core.users.user_id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    impact_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    root_cause: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    root_cause_confirmed_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey(
            "core.users.user_id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    root_cause_confirmed_at: Mapped[datetime | None] = mapped_column(
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
        nullable=False,
    )

    events: Mapped[list["IncidentEvent"]] = relationship(
        "IncidentEvent",
        back_populates="incident",
        cascade="all, delete-orphan",
    )

    investigations: Mapped[list["Investigation"]] = relationship(
        "Investigation",
        back_populates="incident",
        cascade="all, delete-orphan",
    )

    risk_predictions: Mapped[list["RiskPrediction"]] = relationship(
        "RiskPrediction",
        back_populates="incident",
        cascade="all, delete-orphan",
    )

    intelligence_records: Mapped[list["IncidentIntelligence"]] = relationship(
        "IncidentIntelligence",
        back_populates="incident",
        cascade="all, delete-orphan",
    )

    remediations: Mapped[list["RemediationAction"]] = relationship(
        "RemediationAction",
        back_populates="incident",
        cascade="all, delete-orphan",
    )

    service: Mapped["Service"] = relationship(
        "Service",
        back_populates="incidents",
    )

    tickets: Mapped[list["Ticket"]] = relationship(
        "Ticket",
        back_populates="incident",
        cascade="all, delete-orphan",
    )