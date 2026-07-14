# -*- coding: utf-8 -*-
from sqlalchemy import Column, Integer, String, Date, ForeignKey, Numeric, Boolean, DateTime
from sqlalchemy.orm import relationship

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "core-kernel")))
from db import Base, MultiTenantMixin


class Department(Base, MultiTenantMixin):
    """Business departments."""
    __tablename__ = "hr_departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    code = Column(String, nullable=True)
    parent_id = Column(Integer, ForeignKey("hr_departments.id"), nullable=True)


class Position(Base, MultiTenantMixin):
    """Job positions and rank grades."""
    __tablename__ = "hr_positions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    department_id = Column(Integer, ForeignKey("hr_departments.id"), nullable=True)
    grade = Column(String, nullable=True)


class Employee(Base, MultiTenantMixin):
    """Decoupled HR Employee details."""
    __tablename__ = "hr_employees"

    id = Column(Integer, primary_key=True, index=True)
    employee_no = Column(String, unique=True, index=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, nullable=True, index=True)
    phone = Column(String, nullable=True)
    location = Column(String, nullable=True)
    department_id = Column(Integer, ForeignKey("hr_departments.id"), nullable=True)
    position_id = Column(Integer, ForeignKey("hr_positions.id"), nullable=True)
    manager_id = Column(Integer, ForeignKey("hr_employees.id"), nullable=True)
    user_id = Column(Integer, nullable=True)
    joined_date = Column(Date, nullable=True)
    grade = Column(String, nullable=True)
    bank = Column(String, nullable=True)
    iban = Column(String, nullable=True)
    portal_access = Column(Boolean, default=False, nullable=False)
    single_device = Column(String, nullable=True)
    status = Column(String, default="active", nullable=False)  # active | suspended | terminated
    is_active = Column(Boolean, default=True, nullable=False)


class Contract(Base, MultiTenantMixin):
    """Standard employment agreements."""
    __tablename__ = "hr_contracts"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("hr_employees.id"), nullable=False)
    contract_type = Column(String, default="full_time", nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    base_salary = Column(Numeric(12, 2), nullable=False)
    currency = Column(String, default="JOD", nullable=False)
    weekly_hours = Column(Numeric(5, 2), default=48.0, nullable=False)


class Leave(Base, MultiTenantMixin):
    """Leaves and vacation logs."""
    __tablename__ = "hr_leaves"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("hr_employees.id"), nullable=False)
    leave_type = Column(String, nullable=False)  # annual | sick | unpaid | maternity
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    days = Column(Numeric(4, 1), nullable=False)
    status = Column(String, default="draft")  # draft | approved | rejected


class Attendance(Base, MultiTenantMixin):
    """Daily check-in and check-out logs."""
    __tablename__ = "hr_attendance"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("hr_employees.id"), nullable=False)
    date = Column(Date, nullable=False)
    check_in = Column(DateTime, nullable=True)
    check_out = Column(DateTime, nullable=True)
    status = Column(String, default="present")  # present | late | absent


class Payslip(Base, MultiTenantMixin):
    """Historical record of computed employee wages."""
    __tablename__ = "hr_payslips"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("hr_employees.id"), nullable=False)
    period = Column(String, nullable=False)  # e.g., "2026-07"
    gross = Column(Numeric(12, 2), nullable=False)
    employee_social_security = Column(Numeric(12, 2), nullable=False)
    employer_social_security = Column(Numeric(12, 2), nullable=False)
    income_tax = Column(Numeric(12, 2), nullable=False)
    net = Column(Numeric(12, 2), nullable=False)
    status = Column(String, default="draft")  # draft | posted
