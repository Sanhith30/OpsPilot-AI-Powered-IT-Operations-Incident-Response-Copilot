from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
class TicketComment(Base):
    __tablename__="ticket_comments"
    ticket_comment_id:Mapped[int]=mapped_column(Integer,primary_key=True)
    ticket_id:Mapped[int]=mapped_column(ForeignKey("core.tickets.ticket_id",ondelete="CASCADE"),nullable=False)
    author_id:Mapped[int]=mapped_column(ForeignKey("core.users.user_id"),nullable=False)
    comment_text:Mapped[str]=mapped_column(Text,nullable=False)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now(),nullable=False)
    ticket:Mapped["Ticket"]=relationship(back_populates="comments")
    author:Mapped["User"]=relationship(back_populates="ticket_comments")
