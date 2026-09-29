from __future__ import annotations
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
class InvestigationFinding(Base):
    __tablename__ = "investigation_findings"

    finding_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    investigation_id: Mapped[int] = mapped_column(ForeignKey("core.investigations.investigation_id", ondelete="CASCADE"), nullable=False)
    finding_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="Finding")
    finding_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    investigation: Mapped["Investigation"] = relationship(back_populates="findings")
    evidence_links: Mapped[list["FindingEvidence"]] = relationship(back_populates="finding", cascade="all, delete-orphan")

    @property
    def evidence_refs(self) -> list[dict[str, Any]]:
        refs = []
        try:
            for link in self.evidence_links or []:
                ev = link.evidence
                if ev:
                    meta = ev.evidence_metadata or {}
                    cit_id = meta.get("citation_id")
                    refs.append(
                        {
                            "evidence_id": ev.evidence_id,
                            "source_type": ev.evidence_type,
                            "source_id": (
                                cit_id
                                if (cit_id and ev.evidence_type == "KNOWLEDGE_BASE")
                                else ev.source_reference
                            ),
                            "relationship_type": link.relationship_type,
                        }
                    )
        except Exception:
            pass
        return refs

