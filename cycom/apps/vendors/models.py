# -*- coding: utf-8 -*-
# Copyright © CyberCom. Licensed for use as part of the CyCom platform.
"""
CyCom ERP — Vendor Management Models (CyProcure)
Supports full supplier onboarding lifecycle:
  draft → submitted → under_review → approved / rejected / suspended
"""
from sqlalchemy import Column, Integer, String, Date, Numeric, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.sql import func

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "core-kernel")))
from db import Base, MultiTenantMixin


class Vendor(Base, MultiTenantMixin):
    """Approved supplier/vendor master record."""
    __tablename__ = "cy_vendors"

    id = Column(Integer, primary_key=True, index=True)
    # Identity
    legal_name = Column(String, nullable=False, index=True)
    trade_name = Column(String, nullable=True)
    legal_name_ar = Column(String, nullable=True)       # Arabic name
    vendor_code = Column(String, nullable=True, index=True, unique=False)
    # Registration
    cr_number = Column(String, nullable=True, index=True)   # Commercial Registration
    cr_expiry = Column(Date, nullable=True)
    tax_number = Column(String, nullable=True)
    # Bank
    bank_name = Column(String, nullable=True)
    bank_branch = Column(String, nullable=True)
    iban = Column(String, nullable=True)
    swift_code = Column(String, nullable=True)
    currency = Column(String, default="JOD", nullable=False)
    # Contact
    contact_name = Column(String, nullable=True)
    contact_email = Column(String, nullable=True)
    contact_phone = Column(String, nullable=True)
    website = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String, nullable=True)
    country_code = Column(String, default="JO", nullable=False)
    # Terms
    payment_terms_days = Column(Integer, default=30, nullable=False)
    credit_limit = Column(Numeric(14, 2), nullable=True)
    category = Column(String, nullable=True)        # goods | services | both
    risk_rating = Column(String, default="medium")  # low | medium | high
    # Approval workflow
    approval_status = Column(String, default="draft", nullable=False, index=True)
    # draft | submitted | under_review | compliance_review | approved | rejected | suspended | expired
    approved_by_id = Column(Integer, nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    # Metadata
    is_active = Column(Boolean, default=True, nullable=False)
    is_preferred = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    notes = Column(Text, nullable=True)


class VendorDocument(Base, MultiTenantMixin):
    """Documents uploaded during vendor onboarding (CR, Tax cert, bank letter, etc.)."""
    __tablename__ = "cy_vendor_documents"

    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("cy_vendors.id", ondelete="CASCADE"), nullable=False, index=True)
    doc_type = Column(String, nullable=False)
    # cr | tax_certificate | bank_letter | iban_certificate | trade_license
    # authorized_id | insurance | food_safety | compliance | other
    original_filename = Column(String, nullable=False)
    storage_path = Column(String, nullable=False)    # UUID-based path on disk
    file_size_bytes = Column(Integer, nullable=True)
    mime_type = Column(String, nullable=True)
    expiry_date = Column(Date, nullable=True)
    uploaded_by_id = Column(Integer, nullable=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_approved = Column(Boolean, nullable=True)     # None=pending, True=OK, False=rejected
    reviewer_note = Column(String, nullable=True)


class VendorContact(Base, MultiTenantMixin):
    """Multiple contact persons per vendor."""
    __tablename__ = "cy_vendor_contacts"

    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("cy_vendors.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    title = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    mobile = Column(String, nullable=True)
    is_primary = Column(Boolean, default=False)
