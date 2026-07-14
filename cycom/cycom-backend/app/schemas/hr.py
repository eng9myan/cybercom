from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class _M(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# Department
class DepartmentBase(BaseModel):
    name: str
    code: Optional[str] = None
    parent_id: Optional[int] = None
    manager_id: Optional[int] = None


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    parent_id: Optional[int] = None
    manager_id: Optional[int] = None


class DepartmentResponse(_M, DepartmentBase):
    id: int
    company_id: int


# Position
class PositionBase(BaseModel):
    title: str
    department_id: Optional[int] = None
    grade: Optional[str] = None


class PositionCreate(PositionBase):
    pass


class PositionUpdate(BaseModel):
    title: Optional[str] = None
    department_id: Optional[int] = None
    grade: Optional[str] = None


class PositionResponse(_M, PositionBase):
    id: int
    company_id: int


# Employee
class EmployeeBase(BaseModel):
    employee_no: str
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    department_id: Optional[int] = None
    position_id: Optional[int] = None
    manager_id: Optional[int] = None
    user_id: Optional[int] = None
    joined_date: Optional[date] = None
    grade: Optional[str] = None
    bank: Optional[str] = None
    iban: Optional[str] = None
    portal_access: bool = False
    single_device: Optional[str] = None
    status: str = "active"


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    department_id: Optional[int] = None
    position_id: Optional[int] = None
    manager_id: Optional[int] = None
    user_id: Optional[int] = None
    joined_date: Optional[date] = None
    grade: Optional[str] = None
    bank: Optional[str] = None
    iban: Optional[str] = None
    portal_access: Optional[bool] = None
    single_device: Optional[str] = None
    status: Optional[str] = None


class EmployeeResponse(_M, EmployeeBase):
    id: int
    company_id: int
    created_at: datetime


# Contract
class ContractBase(BaseModel):
    employee_id: int
    contract_type: str = "full_time"
    start_date: date
    end_date: Optional[date] = None
    base_salary: Decimal
    currency: str = "JOD"
    weekly_hours: Decimal = Decimal("48")
    status: str = "active"


class ContractCreate(ContractBase):
    pass


class ContractUpdate(BaseModel):
    contract_type: Optional[str] = None
    end_date: Optional[date] = None
    base_salary: Optional[Decimal] = None
    weekly_hours: Optional[Decimal] = None
    status: Optional[str] = None


class ContractResponse(_M, ContractBase):
    id: int
    company_id: int


# Leave
class LeaveTypeBase(BaseModel):
    name: str
    code: str
    paid: bool = True
    annual_entitlement_days: Decimal = Decimal("0")


class LeaveTypeCreate(LeaveTypeBase):
    pass


class LeaveTypeResponse(_M, LeaveTypeBase):
    id: int
    company_id: int


class LeaveRequestBase(BaseModel):
    employee_id: int
    leave_type_id: int
    start_date: date
    end_date: date
    days: Decimal
    reason: Optional[str] = None


class LeaveRequestCreate(LeaveRequestBase):
    pass


class LeaveRequestUpdate(BaseModel):
    status: Optional[str] = None
    reason: Optional[str] = None


class LeaveRequestResponse(_M, LeaveRequestBase):
    id: int
    company_id: int
    status: str
