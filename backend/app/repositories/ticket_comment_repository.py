from app.models.ticket_comment import TicketComment
class TicketCommentRepository:
    def __init__(self, db): self.db=db
    def add(self, comment): self.db.add(comment); return comment
