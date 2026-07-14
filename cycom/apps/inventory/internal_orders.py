# -*- coding: utf-8 -*-
# Copyright © CyberCom. Licensed for use as part of the CyCom platform.
"""
CyCom ERP — Internal Order (Branch → Warehouse) Models (CyInventory)
Implements branch-to-warehouse multi-item ordering with partial fulfillment and pending tracking.
"""
from sqlalchemy import Column, Integer, String, Date, Numeric, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.sql import func

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "core-kernel")))
from db import Base, MultiTenantMixin


class InternalOrder(Base, MultiTenantMixin):
    """
    Multi-item internal replenishment order from a branch to the warehouse.
    A branch may submit one order containing many product lines.
    """
    __tablename__ = "cy_internal_orders"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)        # IO/2026/BRANCH1/0001
    branch_id = Column(Integer, nullable=False, index=True)
    warehouse_id = Column(Integer, nullable=True, index=True)
    requested_by_id = Column(Integer, nullable=True)         # Employee who submitted
    required_date = Column(Date, nullable=True)
    priority = Column(String, default="normal")              # low | normal | high | urgent
    state = Column(String, default="draft", nullable=False, index=True)
    # draft | submitted | warehouse_review | approved | allocated | partially_allocated
    # picking | ready | dispatched | partially_received | received | closed | cancelled
    notes = Column(Text, nullable=True)
    warehouse_notes = Column(Text, nullable=True)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    dispatched_at = Column(DateTime(timezone=True), nullable=True)
    received_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class InternalOrderLine(Base, MultiTenantMixin):
    """
    Individual product line on an internal order.
    Tracks the full lifecycle: requested → allocated → shipped → received.
    Pending = requested - shipped (never silently closed).
    """
    __tablename__ = "cy_internal_order_lines"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("cy_internal_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, nullable=False)
    product_name = Column(String, nullable=False)            # Denormalized for reporting
    product_code = Column(String, nullable=True)
    uom = Column(String, default="unit")

    # Quantity tracking (all non-negative)
    requested_qty = Column(Numeric(12, 3), nullable=False)
    available_qty = Column(Numeric(12, 3), nullable=True)    # Warehouse checks this
    allocated_qty = Column(Numeric(12, 3), default=0)        # Committed by warehouse
    shipped_qty = Column(Numeric(12, 3), default=0)          # Actually dispatched
    received_qty = Column(Numeric(12, 3), default=0)         # Branch confirmed receipt
    rejected_qty = Column(Numeric(12, 3), default=0)         # Rejected on receipt
    pending_qty = Column(Numeric(12, 3), default=0)          # Still unfulfilled — NEVER auto-closed

    # Status per line
    line_state = Column(String, default="pending", nullable=False)
    # pending | allocated | partially_shipped | shipped | received | rejected | cancelled
    warehouse_note = Column(String, nullable=True)
    pending_reason = Column(String, nullable=True)           # Why pending (out_of_stock | quality | etc.)
    expected_availability = Column(Date, nullable=True)
    substitute_product_id = Column(Integer, nullable=True)   # Warehouse suggests substitute


class InternalOrderDiscrepancy(Base, MultiTenantMixin):
    """
    Records discrepancies when branch receives less than what was dispatched.
    Triggers an investigation task.
    """
    __tablename__ = "cy_internal_order_discrepancies"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("cy_internal_orders.id"), nullable=False, index=True)
    line_id = Column(Integer, ForeignKey("cy_internal_order_lines.id"), nullable=False)
    shipped_qty = Column(Numeric(12, 3), nullable=False)
    received_qty = Column(Numeric(12, 3), nullable=False)
    difference_qty = Column(Numeric(12, 3), nullable=False)
    reason = Column(String, nullable=True)
    reported_by_id = Column(Integer, nullable=True)
    investigation_status = Column(String, default="open")    # open | investigating | resolved
    resolution = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
