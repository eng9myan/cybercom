from sqlalchemy import Column, String, ForeignKey, Integer, Numeric, Date

from app.db.base import BaseEntity


class SalesOrder(BaseEntity):
    __tablename__ = "sales_orders"
    reference = Column(String, unique=True, index=True, nullable=False)
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=False, index=True)
    order_date = Column(Date, nullable=False)
    delivery_date = Column(Date, nullable=True)
    subtotal = Column(Numeric(14, 2), default=0, nullable=False)
    tax_total = Column(Numeric(14, 2), default=0, nullable=False)
    total = Column(Numeric(14, 2), default=0, nullable=False)
    status = Column(String, default="Draft", nullable=False)  # Draft|Pending Approval|Confirmed|Delivered|Cancelled


class SalesOrderLine(BaseEntity):
    __tablename__ = "sales_order_lines"
    order_id = Column(Integer, ForeignKey("sales_orders.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Numeric(14, 3), nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    discount_pct = Column(Numeric(5, 2), default=0, nullable=False)
    tax_rate = Column(Numeric(5, 4), default=0, nullable=False)
    subtotal = Column(Numeric(14, 2), default=0, nullable=False)


class DiscountException(BaseEntity):
    __tablename__ = "sales_discount_exceptions"
    order_id = Column(Integer, ForeignKey("sales_orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    standard_price = Column(Numeric(12, 2), nullable=False)
    offered_price = Column(Numeric(12, 2), nullable=False)
    discount_pct = Column(Numeric(5, 2), nullable=False)
    allowed_limit_pct = Column(Numeric(5, 2), nullable=False)
    status = Column(String, default="pending", nullable=False)  # pending|approved|rejected
    approved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
