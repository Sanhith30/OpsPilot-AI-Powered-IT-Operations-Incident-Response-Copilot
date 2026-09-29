from __future__ import annotations
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
class InvestigationFeedback(Base):
    __tablename__="investigation_feedback"
    feedback_id:Mapped[int]=mapped_column(Integer,primary_key=True)
    investigation_id:Mapped[int]=mapped_column(ForeignKey("core.investigations.investigation_id",ondelete="CASCADE"),nullable=False)
    user_id: Mapped[int] = mapped_column("submitted_by", ForeignKey("core.users.user_id"), nullable=False)
    rating:Mapped[int]=mapped_column(Integer,nullable=False)
    feedback_text:Mapped[str|None]=mapped_column(Text)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now(),nullable=False)
    investigation:Mapped["Investigation"]=relationship(back_populates="feedback")
    user:Mapped["User"]=relationship(back_populates="investigation_feedback")
