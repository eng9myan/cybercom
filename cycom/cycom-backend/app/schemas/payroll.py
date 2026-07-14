from datetime import date
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class _M(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class SalaryStructureBase(BaseModel):
    name: str
    code: str
    base_currency: str = "JOD"


class SalaryStructureCreate(SalaryStructureBase):
    pass


class SalaryStructureResponse(_M, SalaryStructureBase):
    id: int
    company_id: int


class PayrollDeductionBase(BaseModel):
    code: str
    name: str
    deduction_type: str = "fixed"
    rate: Decimal = Decimal("0")


class PayrollDeductionCreate(PayrollDeductionBase):
    pass


class PayrollDeductionResponse(_M, PayrollDeductionBase):
    id: int
    company_id: int


class OvertimeClaimBase(BaseModel):
    employee_id: int
    hours: Decimal
    rate_per_hour: Decimal
    multiplier: Decimal = Decimal("1.5")
    date: date


class OvertimeClaimCreate(OvertimeClaimBase):
    pass


class OvertimeClaimUpdate(BaseModel):
    status: Optional[str] = None


class OvertimeClaimResponse(_M, OvertimeClaimBase):
    id: int
    company_id: int
    status: str


class PayslipLineBase(BaseModel):
    code: str
    label: str
    line_type: str = "earning"
    amount: Decimal


class PayslipLineCreate(PayslipLineBase):
    pass


class PayslipLineResponse(_M, PayslipLineBase):
    id: int
    payslip_id: int


class PayslipGenerateRequest(BaseModel):
    employee_id: int
    period: str
    base_salary: Decimal
    overtime_hours: Decimal = Decimal("0")
    lateness_minutes: int = 0
    allowances: Decimal = Decimal("0")
    other_deductions: Decimal = Decimal("0")


class PayslipResponse(_M):
    id: int
    company_id: int
    employee_id: int
    period: str
    base_salary: Decimal
    overtime_amount: Decimal
    allowances: Decimal
    lateness_deduction: Decimal
    other_deductions: Decimal
    net_salary: Decimal
    status: str


class PayslipApprove(BaseModel):
    status: str  # Approved | Paid
