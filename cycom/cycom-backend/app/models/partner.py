from sqlalchemy import Column, String, Boolean

from app.db.base import BaseEntity


class Partner(BaseEntity):
    """Unified contact: customer, vendor, or both."""

    __tablename__ = "partners"
    name = Column(String, nullable=False, index=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    address = Column(String, nullable=True)
    tax_number = Column(String, nullable=True)
    is_customer = Column(Boolean, default=False, nullable=False)
    is_vendor = Column(Boolean, default=False, nullable=False)
    payment_terms = Column(String, default="net_30", nullable=False)
