from __future__ import annotations
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
class FindingEvidence(Base):
    __tablename__="finding_evidence"
    finding_id:Mapped[int]=mapped_column(ForeignKey("core.investigation_findings.finding_id",ondelete="CASCADE"),primary_key=True)
    evidence_id:Mapped[int]=mapped_column(ForeignKey("core.investigation_evidence.evidence_id",ondelete="CASCADE"),primary_key=True)
    relationship_type:Mapped[str]=mapped_column(String(30),nullable=False)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now(),nullable=False)
    finding:Mapped["InvestigationFinding"]=relationship(back_populates="evidence_links")
    evidence:Mapped["InvestigationEvidence"]=relationship(back_populates="finding_links")

    @property
    def citation_id(self) -> str | None:
        try:
            if self.evidence and self.evidence.evidence_metadata:
                return self.evidence.evidence_metadata.get("citation_id")
        except Exception:
            pass
        return None

