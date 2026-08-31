from decimal import Decimal

from products.cycom.payroll.models import AttendanceRecord, Payslip
from products.cycom.payroll.rules import monthly_income_tax, social_security


def compute_payslip(*, payroll_run, employee, contract):
    """
    Full monthly payslip: overtime/lateness (from attendance) + statutory
    deductions (social security + income tax). Idempotent — re-running
    recomputes and overwrites the draft payslip for this run/employee.

        gross = base + allowances + overtime
        net   = gross - late - social_security_employee - income_tax
    """
    records = AttendanceRecord.objects.filter(
        tenant_id=employee.tenant_id,
        employee=employee,
        date__gte=payroll_run.period_start,
        date__lte=payroll_run.period_end,
    )
    total_overtime_minutes = sum((r.overtime_minutes for r in records), 0)
    total_late_minutes = sum((r.late_minutes for r in records), 0)

    hourly_rate = contract.hourly_rate
    overtime_amount = ((Decimal(total_overtime_minutes) / 60) * hourly_rate * contract.overtime_multiplier).quantize(Decimal("0.01"))
    late_deduction = ((Decimal(total_late_minutes) / 60) * hourly_rate).quantize(Decimal("0.01"))

    allowances_total = contract.housing_allowance + contract.transport_allowance
    gross_pay = (contract.base_salary + allowances_total + overtime_amount).quantize(Decimal("0.01"))

    # Social security is on the gross subject wage; income tax (Jordan) is on
    # BASIC salary against the employee's personal exemption.
    ss_employee, ss_employer = social_security(gross_pay)
    income_tax = monthly_income_tax(
        contract.base_salary,
        marital=employee.marital,
        spouse_employed=employee.spouse_employed,
    )

    net_pay = (gross_pay - late_deduction - ss_employee - income_tax).quantize(Decimal("0.01"))

    payslip, _ = Payslip.objects.update_or_create(
        payroll_run=payroll_run,
        employee=employee,
        defaults=dict(
            tenant_id=employee.tenant_id,
            contract=contract,
            base_salary=contract.base_salary,
            allowances_total=allowances_total,
            overtime_amount=overtime_amount,
            late_deduction=late_deduction,
            social_security_employee=ss_employee,
            social_security_employer=ss_employer,
            income_tax=income_tax,
            gross_pay=gross_pay,
            net_pay=net_pay,
            status="draft",
        ),
    )
    return payslip
