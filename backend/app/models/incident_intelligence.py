from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class IncidentIntelligence(Base):
    __tablename__ = "incident_intelligence"

    intelligence_id: Mapped[int] = mapped_column(
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

    investigation_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "core.investigations.investigation_id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    incident_summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    correlated_signals: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    probable_root_causes: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    impact_assessment: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    risk_assessment: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    recommended_actions: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    operational_decision: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    overall_confidence: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
    )

    model_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    model_version: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    incident: Mapped["Incident"] = relationship(
        "Incident",
        back_populates="intelligence_records",
    )

    investigation: Mapped["Investigation"] = relationship(
        "Investigation",
        back_populates="intelligence_records",
    )

    remediations: Mapped[list["RemediationAction"]] = relationship(
        "RemediationAction",
        back_populates="intelligence",
    )
