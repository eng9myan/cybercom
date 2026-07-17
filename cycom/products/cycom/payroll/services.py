from decimal import Decimal

from products.cycom.payroll.models import AttendanceRecord, Payslip


def compute_payslip(*, payroll_run, employee, contract):
    """
    Overtime/lateness rule engine: aggregates attendance in the run's period,
    converts minutes to money via the contract's hourly_rate. Idempotent —
    re-running recomputes and overwrites the draft payslip for this run/employee.
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
    overtime_amount = (Decimal(total_overtime_minutes) / 60) * hourly_rate * contract.overtime_multiplier
    late_deduction = (Decimal(total_late_minutes) / 60) * hourly_rate

    overtime_amount = overtime_amount.quantize(Decimal("0.01"))
    late_deduction = late_deduction.quantize(Decimal("0.01"))

    allowances_total = contract.housing_allowance + contract.transport_allowance
    gross_pay = contract.base_salary + allowances_total + overtime_amount
    net_pay = gross_pay - late_deduction

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
            gross_pay=gross_pay,
            net_pay=net_pay,
            status="draft",
        ),
    )
    return payslip
