from sqlalchemy import Column, String, ForeignKey, Integer, Numeric, DateTime
from sqlalchemy.sql import func

from app.db.base import BaseEntity


class Warehouse(BaseEntity):
    __tablename__ = "warehouses"
    name = Column(String, nullable=False, index=True)
    code = Column(String, nullable=False)
    address = Column(String, nullable=True)


class StockLevel(BaseEntity):
    __tablename__ = "stock_levels"
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    quantity = Column(Numeric(14, 3), default=0, nullable=False)


class StockTransfer(BaseEntity):
    __tablename__ = "stock_transfers"
    reference = Column(String, unique=True, index=True, nullable=False)
    source_warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    destination_warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    sent_qty = Column(Numeric(14, 3), nullable=False)
    received_qty = Column(Numeric(14, 3), default=0, nullable=False)
    status = Column(String, default="Pending", nullable=False)  # Pending|Dispatched|Discrepancy|Resolved
    discrepancy_reason = Column(String, nullable=True)
    dispatched_at = Column(DateTime(timezone=True), nullable=True)
    received_at = Column(DateTime(timezone=True), nullable=True)


class StockMove(BaseEntity):
    __tablename__ = "stock_moves"
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    quantity = Column(Numeric(14, 3), nullable=False)  # signed (+ in, - out)
    reason = Column(String, nullable=False)  # transfer_in|transfer_out|pos_sale|adjustment|...
    source_doc_type = Column(String, nullable=True)
    source_doc_id = Column(Integer, nullable=True)
    moved_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
