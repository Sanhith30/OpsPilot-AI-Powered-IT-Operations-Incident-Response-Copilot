from __future__ import annotations
from datetime import datetime
from typing import Any
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
class InvestigationEvidence(Base):
    __tablename__ = "investigation_evidence"

    evidence_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    investigation_id: Mapped[int] = mapped_column(ForeignKey("core.investigations.investigation_id", ondelete="CASCADE"), nullable=False)
    tool_call_id: Mapped[int | None] = mapped_column(ForeignKey("core.tool_calls.tool_call_id", ondelete="SET NULL"))
    evidence_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source: Mapped[str] = mapped_column("source_name", String(150), nullable=False)
    source_reference: Mapped[str | None] = mapped_column(String(255))
    content: Mapped[str] = mapped_column("evidence_text", Text, nullable=False)
    evidence_metadata: Mapped[dict[str, Any] | None] = mapped_column("structured_data", JSONB)
    collected_at: Mapped[datetime | None] = mapped_column("observed_at", DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    investigation: Mapped["Investigation"] = relationship(back_populates="evidence")
    tool_call: Mapped["ToolCall | None"] = relationship(back_populates="evidence")
    finding_links: Mapped[list["FindingEvidence"]] = relationship(back_populates="evidence", cascade="all, delete-orphan")
