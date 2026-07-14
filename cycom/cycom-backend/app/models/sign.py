from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.db.base import Base


class SignTemplate(Base):
    __tablename__ = "sign_templates"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    name = Column(String, index=True, nullable=False)
    file_path = Column(String, nullable=False)
    fields_config = Column(JSON, default=list, nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class SignRequest(Base):
    __tablename__ = "sign_requests"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    template_id = Column(Integer, ForeignKey("sign_templates.id"), nullable=False)
    token = Column(String, unique=True, index=True, nullable=False)
    status = Column(String, default="Sent", nullable=False)  # Sent | Viewed | Signed | Cancelled
    signers = Column(JSON, default=list, nullable=False)
    signed_document_path = Column(String, nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
