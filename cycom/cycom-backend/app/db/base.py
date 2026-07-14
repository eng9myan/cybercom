from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Boolean
from sqlalchemy.orm import declarative_base, declared_attr
from sqlalchemy.sql import func

Base = declarative_base()


class TimestampMixin:
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class AuditMixin:
    @declared_attr
    def created_by_id(cls):
        return Column(Integer, ForeignKey("users.id"), nullable=True)

    @declared_attr
    def updated_by_id(cls):
        return Column(Integer, ForeignKey("users.id"), nullable=True)


class CompanyScopedMixin:
    @declared_attr
    def company_id(cls):
        return Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)


class SoftDeleteMixin:
    is_active = Column(Boolean, default=True, nullable=False)


class BaseEntity(Base, TimestampMixin, AuditMixin, CompanyScopedMixin, SoftDeleteMixin):
    """Standard ERP entity: id + company scoping + timestamps + audit + soft delete."""

    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)
