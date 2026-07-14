# -*- coding: utf-8 -*-
# Copyright © CyberCom. Licensed for use as part of the CyCom platform.
"""
CyCom ERP — Procurement Models (CyProcure)
Purchase Requests → RFQ → Purchase Orders → Goods Receipt → Vendor Invoice → 3-Way Match
"""
from sqlalchemy import Column, Integer, String, Date, Numeric, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.sql import func

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "core-kernel")))
from db import Base, MultiTenantMixin


class PurchaseRequest(Base, MultiTenantMixin):
    """Multi-item purchase request submitted by a department or branch."""
    __tablename__ = "cy_purchase_requests"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)          # PR/2026/0001
    requester_id = Column(Integer, nullable=False)             # Employee ID
    department_id = Column(Integer, nullable=True)
    branch_id = Column(Integer, nullable=True)
    required_date = Column(Date, nullable=True)
    priority = Column(String, default="normal")                # low | normal | high | urgent
    state = Column(String, default="draft", nullable=False, index=True)
    # draft | submitted | approved | rejected | converted
    justification = Column(Text, nullable=True)
    budget_code = Column(String, nullable=True)
    approved_by_id = Column(Integer, nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    notes = Column(Text, nullable=True)


class PurchaseRequestLine(Base, MultiTenantMixin):
    """Line items on a purchase request."""
    __tablename__ = "cy_purchase_request_lines"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("cy_purchase_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, nullable=True)
    description = Column(String, nullable=False)
    qty = Column(Numeric(12, 3), nullable=False, default=1)
    uom = Column(String, default="unit")
    estimated_unit_price = Column(Numeric(14, 3), nullable=True)
    preferred_vendor_id = Column(Integer, nullable=True)
    delivery_branch_id = Column(Integer, nullable=True)
    notes = Column(String, nullable=True)


class PurchaseOrder(Base, MultiTenantMixin):
    """Full purchase order sent to an approved vendor."""
    __tablename__ = "cy_purchase_orders"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)          # PO/2026/0001
    vendor_id = Column(Integer, ForeignKey("cy_vendors.id"), nullable=False, index=True)
    purchase_request_id = Column(Integer, nullable=True)       # Source PR if any
    order_date = Column(Date, nullable=False)
    delivery_date = Column(Date, nullable=True)
    delivery_branch_id = Column(Integer, nullable=True)
    currency = Column(String, default="JOD", nullable=False)
    amount_untaxed = Column(Numeric(14, 2), default=0)
    amount_tax = Column(Numeric(14, 2), default=0)
    amount_total = Column(Numeric(14, 2), default=0)
    state = Column(String, default="draft", nullable=False, index=True)
    # draft | sent | to_approve | purchase | received | invoiced | done | cancel
    payment_terms_days = Column(Integer, default=30)
    approved_by_id = Column(Integer, nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_by_id = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    notes = Column(Text, nullable=True)


class PurchaseOrderLine(Base, MultiTenantMixin):
    """Line items on a purchase order."""
    __tablename__ = "cy_purchase_order_lines"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("cy_purchase_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, nullable=True)
    description = Column(String, nullable=False)
    qty_ordered = Column(Numeric(12, 3), nullable=False)
    qty_received = Column(Numeric(12, 3), default=0)
    qty_billed = Column(Numeric(12, 3), default=0)
    qty_pending = Column(Numeric(12, 3), default=0)           # undelivered remainder
    uom = Column(String, default="unit")
    unit_price = Column(Numeric(14, 3), nullable=False)
    discount_pct = Column(Numeric(5, 2), default=0)
    tax_pct = Column(Numeric(5, 2), default=0)
    line_total = Column(Numeric(14, 2), nullable=False)
    product_code = Column(String, nullable=True)              # Vendor product code


class GoodsReceipt(Base, MultiTenantMixin):
    """Warehouse goods receipt note — records what physically arrived."""
    __tablename__ = "cy_goods_receipts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)          # GRN/2026/0001
    purchase_order_id = Column(Integer, ForeignKey("cy_purchase_orders.id"), nullable=False, index=True)
    received_date = Column(Date, nullable=False)
    received_by_id = Column(Integer, nullable=True)
    warehouse_id = Column(Integer, nullable=True)
    state = Column(String, default="draft")                    # draft | confirmed | validated
    delivery_note_number = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class GoodsReceiptLine(Base, MultiTenantMixin):
    """Individual line items received in a GRN."""
    __tablename__ = "cy_goods_receipt_lines"

    id = Column(Integer, primary_key=True, index=True)
    receipt_id = Column(Integer, ForeignKey("cy_goods_receipts.id", ondelete="CASCADE"), nullable=False, index=True)
    po_line_id = Column(Integer, ForeignKey("cy_purchase_order_lines.id"), nullable=False)
    qty_received = Column(Numeric(12, 3), nullable=False)
    qty_accepted = Column(Numeric(12, 3), nullable=False)
    qty_rejected = Column(Numeric(12, 3), default=0)
    rejection_reason = Column(String, nullable=True)
    lot_number = Column(String, nullable=True)
    expiry_date = Column(Date, nullable=True)
    quality_status = Column(String, default="accepted")        # accepted | quarantine | rejected


class VendorBill(Base, MultiTenantMixin):
    """Vendor invoice received against a purchase order."""
    __tablename__ = "cy_vendor_bills"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)          # BILL/2026/0001
    vendor_id = Column(Integer, ForeignKey("cy_vendors.id"), nullable=False, index=True)
    purchase_order_id = Column(Integer, nullable=True)
    vendor_invoice_number = Column(String, nullable=True, index=True)
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=True)
    currency = Column(String, default="JOD")
    amount_untaxed = Column(Numeric(14, 2), default=0)
    amount_tax = Column(Numeric(14, 2), default=0)
    amount_total = Column(Numeric(14, 2), default=0)
    amount_paid = Column(Numeric(14, 2), default=0)
    state = Column(String, default="draft", nullable=False, index=True)
    # draft | posted | in_payment | paid | cancelled | disputed
    match_status = Column(String, nullable=True)               # matched | partial | unmatched
    approved_by_id = Column(Integer, nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    attachment_path = Column(String, nullable=True)            # PDF storage path
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    notes = Column(Text, nullable=True)
