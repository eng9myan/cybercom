from sqlalchemy import Column, String, ForeignKey, Integer, Numeric, Date

from app.db.base import BaseEntity


class PurchaseOrder(BaseEntity):
    __tablename__ = "purchase_orders"
    reference = Column(String, unique=True, index=True, nullable=False)
    vendor_id = Column(Integer, ForeignKey("partners.id"), nullable=False, index=True)
    order_date = Column(Date, nullable=False)
    expected_date = Column(Date, nullable=True)
    subtotal = Column(Numeric(14, 2), default=0, nullable=False)
    tax_total = Column(Numeric(14, 2), default=0, nullable=False)
    total = Column(Numeric(14, 2), default=0, nullable=False)
    status = Column(String, default="Draft", nullable=False)  # Draft|RFQ|Confirmed|Received|Cancelled


class PurchaseOrderLine(BaseEntity):
    __tablename__ = "purchase_order_lines"
    order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Numeric(14, 3), nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    tax_rate = Column(Numeric(5, 4), default=0, nullable=False)
    subtotal = Column(Numeric(14, 2), default=0, nullable=False)
