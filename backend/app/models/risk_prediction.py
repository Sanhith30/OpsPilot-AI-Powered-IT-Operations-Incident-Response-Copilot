from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RiskPrediction(Base):
    __tablename__ = "risk_predictions"

    prediction_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    investigation_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "core.investigations.investigation_id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    incident_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "core.incidents.incident_id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    model_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    model_version: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    prediction_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    risk_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
    )

    risk_level: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    prediction_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        "input_features",
        JSONB,
        nullable=True,
    )

    prediction_explanation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    predicted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    incident: Mapped["Incident"] = relationship(
        "Incident",
        back_populates="risk_predictions",
    )

    investigation: Mapped["Investigation"] = relationship(
        "Investigation",
        back_populates="risk_predictions",
    )