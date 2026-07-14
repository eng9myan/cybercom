# -*- coding: utf-8 -*-
# Copyright © CyberCom. Licensed for use as part of the CyCom platform.
"""
CyCom ERP — All missing app models to resolve mocking warnings in rpc.py
Covers: Helpdesk, Fleet, Maintenance, Knowledge, Planning, Quality,
        Marketing, Subscriptions, Expenses, Recruitment
"""
from sqlalchemy import Column, Integer, String, Date, Numeric, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.sql import func

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "core-kernel")))
from db import Base, MultiTenantMixin


# ─── HELPDESK ─────────────────────────────────────────────────────────────────

class HelpdeskTicket(Base, MultiTenantMixin):
    """Customer and internal support tickets."""
    __tablename__ = "cy_helpdesk_tickets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)       # Ticket number
    subject = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    requester_id = Column(Integer, nullable=True)           # Employee or customer
    assignee_id = Column(Integer, nullable=True)
    team_id = Column(Integer, nullable=True)
    ticket_type = Column(String, default="issue")           # issue | question | feature
    priority = Column(String, default="normal")             # low | normal | high | urgent
    state = Column(String, default="new", nullable=False, index=True)
    # new | in_progress | pending | resolved | closed
    sla_deadline = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    branch_id = Column(Integer, nullable=True)
    tags = Column(String, nullable=True)                    # comma-separated


# ─── FLEET ────────────────────────────────────────────────────────────────────

class FleetVehicle(Base, MultiTenantMixin):
    """Company fleet vehicles."""
    __tablename__ = "cy_fleet_vehicles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)       # License plate + description
    license_plate = Column(String, nullable=False, unique=False, index=True)
    make = Column(String, nullable=True)
    model = Column(String, nullable=True)
    year = Column(Integer, nullable=True)
    color = Column(String, nullable=True)
    vin = Column(String, nullable=True)
    fuel_type = Column(String, default="gasoline")          # gasoline | diesel | electric | hybrid
    odometer_km = Column(Numeric(10, 1), default=0)
    state = Column(String, default="active")                # active | maintenance | retired
    driver_id = Column(Integer, nullable=True)              # Employee ID
    branch_id = Column(Integer, nullable=True)
    insurance_expiry = Column(Date, nullable=True)
    license_expiry = Column(Date, nullable=True)
    next_service_km = Column(Numeric(10, 1), nullable=True)
    acquisition_date = Column(Date, nullable=True)
    acquisition_cost = Column(Numeric(14, 2), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FleetMaintenanceLog(Base, MultiTenantMixin):
    """Logs preventative and corrective vehicle maintenance."""
    __tablename__ = "cy_fleet_maintenance_logs"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("cy_fleet_vehicles.id", ondelete="CASCADE"), nullable=False, index=True)
    maintenance_date = Column(Date, nullable=False)
    maintenance_type = Column(String, default="preventative") # preventative | corrective
    cost = Column(Numeric(10, 2), default=0, nullable=False)
    service_provider = Column(String, nullable=True)
    odometer_km = Column(Numeric(10, 1), nullable=True)
    next_service_km = Column(Numeric(10, 1), nullable=True)
    notes = Column(Text, nullable=True)
    tenant_id = Column(Integer, nullable=False, index=True)
    company_id = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FleetFuelLog(Base, MultiTenantMixin):
    """Tracks vehicle fuel consumption logs."""
    __tablename__ = "cy_fleet_fuel_logs"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("cy_fleet_vehicles.id", ondelete="CASCADE"), nullable=False, index=True)
    log_date = Column(Date, nullable=False)
    liters = Column(Numeric(8, 2), nullable=False)
    price_per_liter = Column(Numeric(6, 3), nullable=False)
    total_cost = Column(Numeric(10, 2), nullable=False)
    fuel_station = Column(String, nullable=True)
    odometer_km = Column(Numeric(10, 1), nullable=False)
    tenant_id = Column(Integer, nullable=False, index=True)
    company_id = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ─── MAINTENANCE ──────────────────────────────────────────────────────────────

class MaintenanceEquipment(Base, MultiTenantMixin):
    """Equipment registered for maintenance tracking."""
    __tablename__ = "cy_maintenance_equipment"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    category = Column(String, nullable=True)                # kitchen | refrigeration | vehicle | pos | other
    serial_number = Column(String, nullable=True)
    model = Column(String, nullable=True)
    manufacturer = Column(String, nullable=True)
    branch_id = Column(Integer, nullable=True)
    location = Column(String, nullable=True)
    warranty_expiry = Column(Date, nullable=True)
    last_service_date = Column(Date, nullable=True)
    next_service_date = Column(Date, nullable=True)
    state = Column(String, default="operational")           # operational | maintenance | retired
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class MaintenanceRequest(Base, MultiTenantMixin):
    """Corrective and preventive maintenance work orders."""
    __tablename__ = "cy_maintenance_requests"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    equipment_id = Column(Integer, ForeignKey("cy_maintenance_equipment.id"), nullable=True)
    request_type = Column(String, default="corrective")     # corrective | preventive
    description = Column(Text, nullable=True)
    priority = Column(String, default="normal")
    state = Column(String, default="new", nullable=False)
    # new | in_progress | pending_parts | done | cancelled
    requested_by_id = Column(Integer, nullable=True)
    assigned_to_id = Column(Integer, nullable=True)
    scheduled_date = Column(Date, nullable=True)
    completion_date = Column(Date, nullable=True)
    estimated_hours = Column(Numeric(6, 2), nullable=True)
    actual_hours = Column(Numeric(6, 2), nullable=True)
    vendor_id = Column(Integer, nullable=True)              # External maintenance vendor
    cost = Column(Numeric(10, 2), nullable=True)
    branch_id = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ─── KNOWLEDGE ────────────────────────────────────────────────────────────────

class KnowledgeArticle(Base, MultiTenantMixin):
    """Internal knowledge base articles and policies."""
    __tablename__ = "cy_knowledge_articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    content = Column(Text, nullable=True)
    category = Column(String, nullable=True)
    author_id = Column(Integer, nullable=True)
    state = Column(String, default="draft")                 # draft | published | archived
    is_published = Column(Boolean, default=False)
    view_count = Column(Integer, default=0)
    tags = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


# ─── PLANNING / SHIFTS ────────────────────────────────────────────────────────

class PlanningSlot(Base, MultiTenantMixin):
    """Shift / schedule slot for an employee."""
    __tablename__ = "cy_planning_slots"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, nullable=False, index=True)
    branch_id = Column(Integer, nullable=True)
    department_id = Column(Integer, nullable=True)
    shift_name = Column(String, nullable=True)              # Morning | Evening | Night
    start_datetime = Column(DateTime(timezone=True), nullable=False)
    end_datetime = Column(DateTime(timezone=True), nullable=False)
    break_minutes = Column(Integer, default=0)
    state = Column(String, default="draft")                 # draft | confirmed | done | cancelled
    is_published = Column(Boolean, default=False)
    recurring = Column(Boolean, default=False)
    recurrence_rule = Column(String, nullable=True)         # RRULE iCal format
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ─── QUALITY ──────────────────────────────────────────────────────────────────

class QualityCheck(Base, MultiTenantMixin):
    """Quality inspection checks on products or production batches."""
    __tablename__ = "cy_quality_checks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    product_id = Column(Integer, nullable=True)
    lot_number = Column(String, nullable=True)
    reference = Column(String, nullable=True)               # PO / MO / GRN reference
    check_type = Column(String, default="visual")           # visual | measurement | test | certification
    result = Column(String, nullable=True)                  # pass | fail | pending
    inspector_id = Column(Integer, nullable=True)
    branch_id = Column(Integer, nullable=True)
    inspection_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    state = Column(String, default="pending")               # pending | in_progress | passed | failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ─── MARKETING ────────────────────────────────────────────────────────────────

class MarketingCampaign(Base, MultiTenantMixin):
    """Email / SMS / online marketing campaigns."""
    __tablename__ = "cy_marketing_campaigns"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    campaign_type = Column(String, default="email")         # email | sms | social | aggregator
    subject = Column(String, nullable=True)
    body = Column(Text, nullable=True)
    target_audience = Column(String, nullable=True)
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    state = Column(String, default="draft")                 # draft | scheduled | sent | cancelled
    sent_count = Column(Integer, default=0)
    open_count = Column(Integer, default=0)
    click_count = Column(Integer, default=0)
    created_by_id = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ─── SUBSCRIPTIONS ────────────────────────────────────────────────────────────

class SubscriptionContract(Base, MultiTenantMixin):
    """Recurring subscription contracts with customers."""
    __tablename__ = "cy_subscription_contracts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    customer_id = Column(Integer, nullable=False, index=True)
    product_id = Column(Integer, nullable=True)
    description = Column(String, nullable=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    billing_period = Column(String, default="monthly")      # weekly | monthly | quarterly | annual
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String, default="JOD")
    state = Column(String, default="active")                # draft | active | paused | expired | cancelled
    next_invoice_date = Column(Date, nullable=True)
    auto_renew = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ─── EXPENSES ─────────────────────────────────────────────────────────────────

class Expense(Base, MultiTenantMixin):
    """Employee expense claims."""
    __tablename__ = "cy_expenses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    employee_id = Column(Integer, nullable=False, index=True)
    expense_date = Column(Date, nullable=False)
    category = Column(String, nullable=True)                # travel | meals | supplies | other
    description = Column(String, nullable=True)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String, default="JOD")
    tax_amount = Column(Numeric(12, 2), default=0)
    total_amount = Column(Numeric(12, 2), nullable=False)
    state = Column(String, default="draft")                 # draft | submitted | approved | rejected | paid
    approved_by_id = Column(Integer, nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    receipt_path = Column(String, nullable=True)            # Attached receipt image
    branch_id = Column(Integer, nullable=True)
    project_id = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ─── RECRUITMENT ──────────────────────────────────────────────────────────────

class JobPosition(Base, MultiTenantMixin):
    """Open job positions for recruitment."""
    __tablename__ = "cy_job_positions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    department_id = Column(Integer, nullable=True)
    branch_id = Column(Integer, nullable=True)
    vacancies = Column(Integer, default=1)
    state = Column(String, default="open")                  # open | closed | on_hold
    description = Column(Text, nullable=True)
    requirements = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JobApplicant(Base, MultiTenantMixin):
    """Candidates applying for a job position."""
    __tablename__ = "cy_job_applicants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    position_id = Column(Integer, ForeignKey("cy_job_positions.id"), nullable=True)
    department_id = Column(Integer, nullable=True)
    stage = Column(String, default="new")
    # new | screening | interview | offer | hired | rejected
    priority = Column(String, default="normal")
    expected_salary = Column(Numeric(12, 2), nullable=True)
    source = Column(String, nullable=True)                  # website | referral | agency | linkedin
    interviewer_id = Column(Integer, nullable=True)
    interview_date = Column(DateTime(timezone=True), nullable=True)
    cv_path = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
