from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, Date

from app.db.base import BaseEntity


class SalaryStructure(BaseEntity):
    __tablename__ = "payroll_salary_structures"
    name = Column(String, nullable=False)
    code = Column(String, nullable=False)
    base_currency = Column(String, default="JOD", nullable=False)


class PayrollDeduction(BaseEntity):
    __tablename__ = "payroll_deductions"
    code = Column(String, nullable=False)  # SSC | TAX | LOAN | LATE | ...
    name = Column(String, nullable=False)
    deduction_type = Column(String, default="fixed", nullable=False)  # fixed|percent
    rate = Column(Numeric(8, 4), default=0, nullable=False)


class OvertimeClaim(BaseEntity):
    __tablename__ = "payroll_overtime_claims"
    employee_id = Column(Integer, ForeignKey("hr_employees.id"), nullable=False, index=True)
    hours = Column(Numeric(6, 2), nullable=False)
    rate_per_hour = Column(Numeric(10, 2), nullable=False)
    multiplier = Column(Numeric(4, 2), default=1.5, nullable=False)
    date = Column(Date, nullable=False)
    status = Column(String, default="pending", nullable=False)  # pending|approved|rejected
    approved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)


class Payslip(BaseEntity):
    __tablename__ = "payroll_payslips"
    employee_id = Column(Integer, ForeignKey("hr_employees.id"), nullable=False, index=True)
    period = Column(String, nullable=False, index=True)  # e.g. "June 2026"
    period_start = Column(Date, nullable=True)
    period_end = Column(Date, nullable=True)
    base_salary = Column(Numeric(12, 2), nullable=False)
    overtime_amount = Column(Numeric(12, 2), default=0, nullable=False)
    allowances = Column(Numeric(12, 2), default=0, nullable=False)
    lateness_deduction = Column(Numeric(12, 2), default=0, nullable=False)
    other_deductions = Column(Numeric(12, 2), default=0, nullable=False)
    net_salary = Column(Numeric(12, 2), nullable=False)
    status = Column(String, default="Draft", nullable=False)  # Draft|Approved|Paid


class PayslipLine(BaseEntity):
    __tablename__ = "payroll_payslip_lines"
    payslip_id = Column(Integer, ForeignKey("payroll_payslips.id"), nullable=False, index=True)
    code = Column(String, nullable=False)
    label = Column(String, nullable=False)
    line_type = Column(String, default="earning", nullable=False)  # earning|deduction|employer
    amount = Column(Numeric(12, 2), nullable=False)
