from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func

from app.db.base import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    short_name = Column(String, nullable=False)
    code = Column(String, unique=True, index=True, nullable=False)
    currency = Column(String, default="JOD", nullable=False)
    country_code = Column(String, default="JO", nullable=False)
    type = Column(String, default="commercial", nullable=False)  # retail | commercial | factory
    parent_id = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
