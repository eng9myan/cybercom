from sqlalchemy import Column, Integer, String, Date, ForeignKey, Numeric, Boolean

from app.db.base import BaseEntity


class Department(BaseEntity):
    __tablename__ = "hr_departments"
    name = Column(String, nullable=False, index=True)
    code = Column(String, nullable=True)
    parent_id = Column(Integer, ForeignKey("hr_departments.id"), nullable=True)
    manager_id = Column(Integer, ForeignKey("hr_employees.id"), nullable=True)


class Position(BaseEntity):
    __tablename__ = "hr_positions"
    title = Column(String, nullable=False, index=True)
    department_id = Column(Integer, ForeignKey("hr_departments.id"), nullable=True)
    grade = Column(String, nullable=True)


class Employee(BaseEntity):
    __tablename__ = "hr_employees"
    employee_no = Column(String, unique=True, index=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, nullable=True, index=True)
    phone = Column(String, nullable=True)
    location = Column(String, nullable=True)
    department_id = Column(Integer, ForeignKey("hr_departments.id"), nullable=True)
    position_id = Column(Integer, ForeignKey("hr_positions.id"), nullable=True)
    manager_id = Column(Integer, ForeignKey("hr_employees.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    joined_date = Column(Date, nullable=True)
    grade = Column(String, nullable=True)
    bank = Column(String, nullable=True)
    iban = Column(String, nullable=True)
    portal_access = Column(Boolean, default=False, nullable=False)
    single_device = Column(String, nullable=True)
    status = Column(String, default="active", nullable=False)  # active|suspended|terminated


class Contract(BaseEntity):
    __tablename__ = "hr_contracts"
    employee_id = Column(Integer, ForeignKey("hr_employees.id"), nullable=False, index=True)
    contract_type = Column(String, default="full_time", nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    base_salary = Column(Numeric(12, 2), nullable=False)
    currency = Column(String, default="JOD", nullable=False)
    weekly_hours = Column(Numeric(5, 2), default=48, nullable=False)
    status = Column(String, default="active", nullable=False)


class LeaveType(BaseEntity):
    __tablename__ = "hr_leave_types"
    name = Column(String, nullable=False)
    code = Column(String, nullable=False)
    paid = Column(Boolean, default=True, nullable=False)
    annual_entitlement_days = Column(Numeric(6, 2), default=0, nullable=False)


class LeaveRequest(BaseEntity):
    __tablename__ = "hr_leave_requests"
    employee_id = Column(Integer, ForeignKey("hr_employees.id"), nullable=False, index=True)
    leave_type_id = Column(Integer, ForeignKey("hr_leave_types.id"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    days = Column(Numeric(6, 2), nullable=False)
    reason = Column(String, nullable=True)
    status = Column(String, default="draft", nullable=False)  # draft|submitted|approved|rejected|cancelled
    approved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
