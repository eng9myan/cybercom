"""
Payroll computation — real Australian PAYG withholding + superannuation.
Resident tax brackets (2024–25). Simplified (annualised → monthly); a full STP
implementation would add Medicare levy, HELP, offsets — this is the correct
structure to extend.
"""

from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")
SUPER_RATE = Decimal("0.115")  # 11.5% (2024–25)

# (upper_bound, base_tax_at_lower, marginal_rate, lower_bound)
_BRACKETS = [
    (Decimal("18200"), Decimal("0"), Decimal("0"), Decimal("0")),
    (Decimal("45000"), Decimal("0"), Decimal("0.16"), Decimal("18200")),
    (Decimal("135000"), Decimal("4288"), Decimal("0.30"), Decimal("45000")),
    (Decimal("190000"), Decimal("31288"), Decimal("0.37"), Decimal("135000")),
    (None, Decimal("51638"), Decimal("0.45"), Decimal("190000")),
]


def _q(x):
    return Decimal(x).quantize(CENT, rounding=ROUND_HALF_UP)


def annual_tax(annual_income: Decimal) -> Decimal:
    a = Decimal(annual_income)
    for upper, base, rate, lower in _BRACKETS:
        if upper is None or a <= upper:
            return _q(base + (a - lower) * rate)
    return Decimal("0")


def attendance_for_period(tenant_id, staff, period_start, period_end):
    """
    Pull the attendance figures payroll depends on for a pay period.

    Returns hours worked, paid leave days, and *unpaid* days (unexplained
    absence), which dock pay. This is the single link between Staff Attendance
    and Payroll — payroll never invents hours.
    """
    from products.cyed.staff_attendance.models import StaffAttendanceDay

    days = StaffAttendanceDay.objects.filter(
        tenant_id=tenant_id, staff=staff, date__gte=period_start, date__lte=period_end
    )
    hours = sum((Decimal(d.hours_worked) for d in days), Decimal("0"))
    unpaid = sum((Decimal("1") for d in days if d.status in StaffAttendanceDay.UNPAID), Decimal("0"))
    leave = sum((Decimal("1") for d in days if d.status in ("leave", "sick")), Decimal("0"))
    late_minutes = sum((d.minutes_late for d in days), 0)
    return {
        "hours_worked": _q(hours),
        "unpaid_days": unpaid,
        "leave_days": leave,
        "minutes_late": late_minutes,
        "days_recorded": days.count(),
    }


def salary_components(tenant_id, staff):
    """Active allowances/deductions for a staff member (plus tenant-wide ones)."""
    from django.db.models import Q

    from products.cyed.payroll.models import SalaryComponent

    return SalaryComponent.objects.filter(
        Q(staff=staff) | Q(staff__isnull=True), tenant_id=tenant_id, is_active=True
    )


def compute_payslip(
    *, staff, contract, period_fraction=Decimal("1") / Decimal("12"),
    tenant_id=None, period_start=None, period_end=None, working_days=20,
):
    """
    Compute one payslip. `period_fraction` = share of the year this pay covers
    (default monthly = 1/12). Uses the contract's annual salary × FTE.

    When `tenant_id` + a period are supplied, Staff Attendance is consulted:
    unexplained absences are docked pro-rata, and active salary components are
    applied as allowances/deductions. Each figure is returned as an itemised
    line so the payslip is fully auditable.
    """
    annual = Decimal(contract.annual_salary) * Decimal(contract.fte or 1)
    base_gross = _q(annual * period_fraction)

    lines = [{"kind": "earning", "description": "Base salary", "amount": base_gross}]
    att = {"hours_worked": Decimal("0"), "unpaid_days": Decimal("0"), "leave_days": Decimal("0")}
    unpaid_deduction = Decimal("0")

    if tenant_id and period_start and period_end:
        att = attendance_for_period(tenant_id, staff, period_start, period_end)
        if att["unpaid_days"]:
            daily_rate = base_gross / Decimal(working_days or 20)
            unpaid_deduction = _q(daily_rate * att["unpaid_days"])
            lines.append({
                "kind": "deduction",
                "description": f"Unpaid absence ({att['unpaid_days']:g} day(s))",
                "amount": unpaid_deduction,
            })

    gross = _q(base_gross - unpaid_deduction)

    allowances_total = Decimal("0")
    deductions_total = unpaid_deduction
    if tenant_id:
        for comp in salary_components(tenant_id, staff):
            value = _q(gross * Decimal(comp.amount) / Decimal(100)) if comp.is_percent_of_gross \
                else _q(comp.amount)
            if comp.kind == "allowance":
                allowances_total += value
                gross = _q(gross + value)
                lines.append({"kind": "allowance", "description": comp.description, "amount": value})
            else:
                deductions_total += value
                lines.append({"kind": "deduction", "description": comp.description, "amount": value})

    # Tax is annualised off the actual gross for the period, so docked pay and
    # allowances flow through to withholding rather than being ignored.
    annualised = gross / period_fraction if period_fraction else Decimal("0")
    tax = _q(annual_tax(annualised) * period_fraction)
    sup = _q(gross * SUPER_RATE)
    net = _q(gross - tax - (deductions_total - unpaid_deduction))

    lines.append({"kind": "tax", "description": "PAYG withholding", "amount": tax})
    lines.append({"kind": "super", "description": f"Superannuation ({SUPER_RATE * 100:g}%)", "amount": sup})

    return {
        "gross": gross,
        "paye_tax": tax,
        "superannuation": sup,
        "net": net,
        "hours_worked": att["hours_worked"],
        "unpaid_days": att["unpaid_days"],
        "unpaid_deduction": unpaid_deduction,
        "leave_days": att["leave_days"],
        "allowances_total": allowances_total,
        "deductions_total": deductions_total,
        "lines": lines,
    }
