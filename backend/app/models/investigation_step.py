from __future__ import annotations
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
class InvestigationStep(Base):
    __tablename__="investigation_steps"
    __table_args__=(UniqueConstraint("investigation_id","step_number",name="uq_investigation_step_number"),)
    step_id:Mapped[int]=mapped_column(Integer,primary_key=True)
    investigation_id:Mapped[int]=mapped_column(ForeignKey("core.investigations.investigation_id",ondelete="CASCADE"),nullable=False)
    step_number:Mapped[int]=mapped_column(Integer,nullable=False)
    step_type:Mapped[str]=mapped_column(String(50),nullable=False)
    title:Mapped[str]=mapped_column(String(255),nullable=False)
    description:Mapped[str|None]=mapped_column(Text)
    status:Mapped[str]=mapped_column(String(30),nullable=False)
    started_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True))
    completed_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True))
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now(),nullable=False)
    investigation:Mapped["Investigation"]=relationship(back_populates="steps")
    tool_calls:Mapped[list["ToolCall"]]=relationship(back_populates="step")
