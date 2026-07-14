# -*- coding: utf-8 -*-
from sqlalchemy import Column, Integer, String, Date, ForeignKey, Numeric, Boolean
from sqlalchemy.orm import relationship

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "core-kernel")))
from db import Base, MultiTenantMixin


class Project(Base, MultiTenantMixin):
    """B2B Client Projects."""
    __tablename__ = "proj_projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    code = Column(String, nullable=True)
    partner_id = Column(Integer, nullable=True)  # Link to crm_partners
    status = Column(String, default="active", nullable=False)  # active | completed | paused
    is_active = Column(Boolean, default=True, nullable=False)


class Task(Base, MultiTenantMixin):
    """Task cards associated with Projects."""
    __tablename__ = "proj_tasks"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("proj_projects.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    assignee_id = Column(Integer, nullable=True)
    stage = Column(String, default="todo", nullable=False)  # todo | in_progress | review | done
    priority = Column(String, default="normal", nullable=False)
    due_date = Column(Date, nullable=True)
    estimated_hours = Column(Numeric(6, 2), default=0.0, nullable=False)
    depends_on_task_id = Column(Integer, ForeignKey("proj_tasks.id"), nullable=True)  # Dependency self-relation
    is_active = Column(Boolean, default=True, nullable=False)


class Timesheet(Base, MultiTenantMixin):
    """Timesheet log records matching employee efforts on tasks."""
    __tablename__ = "proj_timesheets"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("proj_tasks.id"), nullable=False, index=True)
    user_id = Column(Integer, nullable=False)
    date = Column(Date, nullable=False)
    hours = Column(Numeric(6, 2), nullable=False)
    notes = Column(String, nullable=True)
    approval_status = Column(String, default="draft")  # draft | submitted | approved | rejected


# =========================================================================
#   PROJECT MILESTONES & BUDGET TRACKING
# =========================================================================

class Milestone(Base, MultiTenantMixin):
    """Project milestones with target deliverables."""
    __tablename__ = "proj_milestones"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("proj_projects.id"), nullable=False)
    name = Column(String, nullable=False)
    due_date = Column(Date, nullable=False)
    status = Column(String, default="pending")  # pending | achieved | missed


class Budget(Base, MultiTenantMixin):
    """Cost and resource budgets compared against actual timesheet outputs."""
    __tablename__ = "proj_budgets"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("proj_projects.id"), nullable=False)
    planned_hours = Column(Numeric(10, 2), default=0.0, nullable=False)
    planned_cost = Column(Numeric(14, 2), default=0.0, nullable=False)
    actual_hours = Column(Numeric(10, 2), default=0.0, nullable=False)
    actual_cost = Column(Numeric(14, 2), default=0.0, nullable=False)
