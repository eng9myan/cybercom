from sqlalchemy import Column, String, ForeignKey, Integer, Numeric, Date, DateTime

from app.db.base import BaseEntity


class Project(BaseEntity):
    __tablename__ = "proj_projects"
    name = Column(String, nullable=False, index=True)
    code = Column(String, nullable=True)
    customer_id = Column(Integer, ForeignKey("partners.id"), nullable=True)
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String, default="active", nullable=False)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)


class Task(BaseEntity):
    __tablename__ = "proj_tasks"
    project_id = Column(Integer, ForeignKey("proj_projects.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    stage = Column(String, default="todo", nullable=False)  # todo|in_progress|review|done|cancelled
    priority = Column(String, default="normal", nullable=False)
    due_date = Column(Date, nullable=True)
    estimated_hours = Column(Numeric(6, 2), default=0, nullable=False)


class Timesheet(BaseEntity):
    __tablename__ = "proj_timesheets"
    task_id = Column(Integer, ForeignKey("proj_tasks.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False)
    hours = Column(Numeric(6, 2), nullable=False)
    notes = Column(String, nullable=True)
