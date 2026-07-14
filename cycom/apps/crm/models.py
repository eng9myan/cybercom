# -*- coding: utf-8 -*-
from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime, Boolean, Date
from sqlalchemy.sql import func
from sqlalchemy.orm import Session

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "core-kernel")))
from db import Base, MultiTenantMixin


class Lead(Base, MultiTenantMixin):
    """B2B sales leads with status and pipeline stage mappings."""
    __tablename__ = "crm_leads"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    contact_name = Column(String, nullable=True)
    contact_email = Column(String, nullable=True)
    contact_phone = Column(String, nullable=True)
    source = Column(String, nullable=True)  # web | email | campaign | call
    expected_revenue = Column(Numeric(14, 2), default=0.0, nullable=False)
    stage = Column(String, default="new", nullable=False)  # new | qualified | proposal | won | lost
    assigned_to_id = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)


class Opportunity(Base, MultiTenantMixin):
    """Promoted opportunities linked to core lead pipeline."""
    __tablename__ = "crm_opportunities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    lead_id = Column(Integer, ForeignKey("crm_leads.id"), nullable=True)
    amount = Column(Numeric(14, 2), default=0.0, nullable=False)
    probability = Column(Numeric(5, 2), default=0.0, nullable=False)  # Percentage (0-100)
    stage = Column(String, default="qualified", nullable=False)


class Activity(Base, MultiTenantMixin):
    """Next actions, follow-ups, or logged communications on leads/deals."""
    __tablename__ = "crm_activities"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("crm_leads.id"), nullable=True)
    activity_type = Column(String, nullable=False)  # call | email | meeting | task
    subject = Column(String, nullable=False)
    notes = Column(String, nullable=True)
    status = Column(String, default="planned", nullable=False)  # planned | completed


# =========================================================================
#   B2B PARTNERS & SALE ORDERS
# =========================================================================

class Partner(Base, MultiTenantMixin):
    """B2B Customer and Vendor profiles."""
    __tablename__ = "crm_partners"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    type = Column(String, default="customer", nullable=False)  # customer | vendor
    email = Column(String, nullable=True, index=True)
    phone = Column(String, nullable=True)
    address = Column(String, nullable=True)
    tax_id = Column(String, nullable=True)
    credit_limit = Column(Numeric(14, 2), default=5000.0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)


class SaleOrder(Base, MultiTenantMixin):
    """B2B Sales Orders."""
    __tablename__ = "crm_sale_orders"

    id = Column(Integer, primary_key=True, index=True)
    number = Column(String, unique=True, index=True, nullable=False)
    partner_id = Column(Integer, ForeignKey("crm_partners.id"), nullable=False)
    date = Column(Date, nullable=False)
    amount_untaxed = Column(Numeric(14, 2), default=0.0, nullable=False)
    amount_tax = Column(Numeric(14, 2), default=0.0, nullable=False)
    amount_total = Column(Numeric(14, 2), default=0.0, nullable=False)
    state = Column(String, default="draft")  # draft | sent | sale | done | cancel


class SaleOrderLine(Base, MultiTenantMixin):
    """Items referenced inside a Sales Order."""
    __tablename__ = "crm_sale_order_lines"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("crm_sale_orders.id"), nullable=False)
    product_id = Column(Integer, nullable=False, index=True)
    name = Column(String, nullable=False)
    qty = Column(Numeric(12, 4), default=1.0, nullable=False)
    price_unit = Column(Numeric(14, 2), default=0.0, nullable=False)
    tax_percent = Column(Numeric(5, 2), default=0.0, nullable=False)
    price_subtotal = Column(Numeric(14, 2), default=0.0, nullable=False)


class CRMWorkflowService:
    """Handles CRM transition logic to financial cycles."""

    @staticmethod
    def convert_lead_to_order(db: Session, lead: Lead, order_number: str, tenant_id: int, company_id: int) -> SaleOrder:
        # 1. Create Partner profile
        partner = Partner(
            name=lead.contact_name or lead.name,
            type="customer",
            email=lead.contact_email,
            phone=lead.contact_phone,
            tenant_id=tenant_id,
            company_id=company_id
        )
        db.add(partner)
        db.commit()
        db.refresh(partner)

        # 2. Create Sale Order
        order = SaleOrder(
            number=order_number,
            partner_id=partner.id,
            date=func.current_date(),
            amount_untaxed=lead.expected_revenue,
            amount_tax=lead.expected_revenue * Decimal("0.16"),  # Default Jordan 16% VAT
            amount_total=lead.expected_revenue * Decimal("1.16"),
            state="sale",
            tenant_id=tenant_id,
            company_id=company_id
        )
        db.add(order)

        # 3. Mark Lead as won
        lead.stage = "won"
        db.commit()
        db.refresh(order)

        return order
from decimal import Decimal
