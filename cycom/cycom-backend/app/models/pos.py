from sqlalchemy import Column, String, ForeignKey, Integer, Numeric, DateTime

from app.db.base import BaseEntity


class PosSession(BaseEntity):
    __tablename__ = "pos_sessions"
    reference = Column(String, unique=True, index=True, nullable=False)
    opened_at = Column(DateTime(timezone=True), nullable=False)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    opening_float = Column(Numeric(12, 2), default=0, nullable=False)
    closing_amount = Column(Numeric(12, 2), nullable=True)
    operator_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String, default="Open", nullable=False)  # Open|Closed


class PosOrder(BaseEntity):
    __tablename__ = "pos_orders"
    session_id = Column(Integer, ForeignKey("pos_sessions.id"), nullable=False, index=True)
    reference = Column(String, unique=True, index=True, nullable=False)
    customer_name = Column(String, default="Walk-in Customer", nullable=False)
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=True)
    subtotal = Column(Numeric(14, 2), default=0, nullable=False)
    tax_total = Column(Numeric(14, 2), default=0, nullable=False)
    total = Column(Numeric(14, 2), default=0, nullable=False)
    payment_method = Column(String, default="cash", nullable=False)  # cash|card|split
    tendered = Column(Numeric(14, 2), default=0, nullable=False)
    change = Column(Numeric(14, 2), default=0, nullable=False)
    order_type = Column(String, default="standard", nullable=False)  # standard|advance|pledge
    deposit = Column(Numeric(14, 2), default=0, nullable=False)
    deadline_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, default="Paid", nullable=False)  # Pending|Paid|Refunded|Fulfilled|Overdue


class PosOrderLine(BaseEntity):
    __tablename__ = "pos_order_lines"
    order_id = Column(Integer, ForeignKey("pos_orders.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Numeric(14, 3), nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    discount_pct = Column(Numeric(5, 2), default=0, nullable=False)
    tax_rate = Column(Numeric(5, 4), default=0, nullable=False)
    subtotal = Column(Numeric(14, 2), default=0, nullable=False)


class PosCashMove(BaseEntity):
    __tablename__ = "pos_cash_moves"
    session_id = Column(Integer, ForeignKey("pos_sessions.id"), nullable=False, index=True)
    move_type = Column(String, nullable=False)  # Cash-In|Cash-Out
    amount = Column(Numeric(12, 2), nullable=False)
    reason = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
