from sqlalchemy import Column, String, ForeignKey, Integer, DateTime

from app.db.base import BaseEntity


class Ticket(BaseEntity):
    __tablename__ = "hd_tickets"
    reference = Column(String, unique=True, index=True, nullable=False)
    subject = Column(String, nullable=False, index=True)
    description = Column(String, nullable=True)
    requester_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    requester_email = Column(String, nullable=True)
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    priority = Column(String, default="normal", nullable=False)  # low|normal|high|urgent
    stage = Column(String, default="new", nullable=False)  # new|in_progress|waiting|resolved|closed
    category = Column(String, nullable=True)


class TicketComment(BaseEntity):
    __tablename__ = "hd_ticket_comments"
    ticket_id = Column(Integer, ForeignKey("hd_tickets.id"), nullable=False, index=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    body = Column(String, nullable=False)
    is_internal = Column(String, default="no", nullable=False)
