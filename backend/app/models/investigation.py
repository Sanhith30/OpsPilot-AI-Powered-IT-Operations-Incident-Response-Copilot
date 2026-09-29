from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Investigation(Base):
    __tablename__ = "investigations"

    investigation_id: Mapped[int] = mapped_column(
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

    # Python name stays "started_by" so the existing
    # service/API code does not need to change.
    # PostgreSQL column is actually "initiated_by".
    started_by: Mapped[int | None] = mapped_column(
        "initiated_by",
        BigInteger,
        ForeignKey(
            "core.users.user_id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    investigation_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    # Python name stays "question".
    # PostgreSQL column is actually "user_question".
    question: Mapped[str] = mapped_column(
        "user_question",
        Text,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    final_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    incident: Mapped["Incident"] = relationship(
        "Incident",
        back_populates="investigations",
    )

    starter: Mapped["User | None"] = relationship(
        "User",
        back_populates="investigations_started",
        foreign_keys=[started_by],
    )

    steps: Mapped[list["InvestigationStep"]] = relationship(
        "InvestigationStep",
        back_populates="investigation",
        cascade="all, delete-orphan",
    )

    tool_calls: Mapped[list["ToolCall"]] = relationship(
        "ToolCall",
        back_populates="investigation",
        cascade="all, delete-orphan",
    )

    evidence: Mapped[list["InvestigationEvidence"]] = relationship(
        "InvestigationEvidence",
        back_populates="investigation",
        cascade="all, delete-orphan",
    )

    findings: Mapped[list["InvestigationFinding"]] = relationship(
        "InvestigationFinding",
        back_populates="investigation",
        cascade="all, delete-orphan",
    )

    risk_predictions: Mapped[list["RiskPrediction"]] = relationship(
        "RiskPrediction",
        back_populates="investigation",
        cascade="all, delete-orphan",
    )

    feedback: Mapped[list["InvestigationFeedback"]] = relationship(
        "InvestigationFeedback",
        back_populates="investigation",
        cascade="all, delete-orphan",
    )

    intelligence_records: Mapped[list["IncidentIntelligence"]] = relationship(
        "IncidentIntelligence",
        back_populates="investigation",
        cascade="all, delete-orphan",
    )

    remediations: Mapped[list["RemediationAction"]] = relationship(
        "RemediationAction",
        back_populates="investigation",
    )

    @property
    def knowledge_evidence(self) -> list[dict[str, Any]]:
        ev_list = []
        try:
            ev_list = self.evidence or []
        except Exception:
            return []

        results = []
        for ev in ev_list:
            if (ev.evidence_type or "").upper() == "KNOWLEDGE_BASE":
                meta = ev.evidence_metadata or {}
                results.append(
                    {
                        "evidence_id": ev.evidence_id,
                        "citation_id": meta.get("citation_id"),
                        "chunk_id": ev.source_reference or meta.get("chunk_id", ""),
                        "document_id": str(meta.get("document_id", "")),
                        "source_name": str(meta.get("source_name") or ev.source or ""),
                        "source_type": str(meta.get("source_type") or "FILE"),
                        "version_number": int(meta.get("version_number", 0)),
                        "score": float(meta.get("score", 0.0)),
                        "title": str(ev.source or meta.get("title", "")),
                        "content": ev.content or "",
                    }
                )
        return results