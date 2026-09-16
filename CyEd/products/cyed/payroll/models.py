from django.db import models

from platform.common.models import BaseModel


class PayrollRun(BaseModel):
    STATUS = [("draft", "Draft"), ("processed", "Processed"), ("paid", "Paid")]

    period_label = models.CharField(max_length=50)  # e.g. "2026-02"
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)
    pay_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default="draft")

    class Meta:
        db_table = "cyed_payroll_runs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Payroll {self.period_label} ({self.status})"


class SalaryComponent(BaseModel):
    """
    A recurring allowance or deduction attached to a staff member (or to every
    staff member when `staff` is null) — e.g. laptop allowance, union fees,
    salary-sacrifice. Applied automatically on each payroll run.
    """

    KIND = [("allowance", "Allowance"), ("deduction", "Deduction")]

    staff = models.ForeignKey(
        "cyed_hr.Staff", on_delete=models.CASCADE, null=True, blank=True, related_name="salary_components"
    )
    kind = models.CharField(max_length=20, choices=KIND, default="allowance")
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_percent_of_gross = models.BooleanField(default=False)
    taxable = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cyed_payroll_salary_components"
        ordering = ["kind", "description"]

    def __str__(self):
        scope = self.staff_id or "all staff"
        return f"{self.kind}: {self.description} ({scope})"


class Payslip(BaseModel):
    PAYMENT_STATUS = [("unpaid", "Unpaid"), ("paid", "Paid"), ("failed", "Failed")]

    payroll_run = models.ForeignKey(PayrollRun, on_delete=models.CASCADE, related_name="payslips")
    staff = models.ForeignKey("cyed_hr.Staff", on_delete=models.CASCADE, related_name="payslips")
    gross = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paye_tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)   # PAYG withholding
    superannuation = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # ── Attendance-derived figures (from cyed_staff_attendance) ──────────────
    hours_worked = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    unpaid_days = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    unpaid_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    leave_days = models.DecimalField(max_digits=5, decimal_places=1, default=0)

    allowances_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    deductions_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # ── Payment history ──────────────────────────────────────────────────────
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default="unpaid")
    paid_on = models.DateField(null=True, blank=True)
    payment_reference = models.CharField(max_length=100, blank=True)
    payment_method = models.CharField(max_length=30, default="bank_transfer")

    class Meta:
        db_table = "cyed_payroll_payslips"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["payroll_run", "staff"], name="uniq_payslip_per_run_staff")
        ]

    def __str__(self):
        return f"Payslip {self.staff_id} {self.net}"


class PayslipLine(BaseModel):
    """An itemised line on a payslip — every figure is traceable to a line."""

    KIND = [
        ("earning", "Earning"), ("allowance", "Allowance"),
        ("deduction", "Deduction"), ("tax", "Tax"), ("super", "Superannuation"),
    ]

    payslip = models.ForeignKey(Payslip, on_delete=models.CASCADE, related_name="lines")
    kind = models.CharField(max_length=20, choices=KIND, default="earning")
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        db_table = "cyed_payroll_payslip_lines"
        ordering = ["kind", "id"]

    def __str__(self):
        return f"{self.kind}: {self.description} {self.amount}"
