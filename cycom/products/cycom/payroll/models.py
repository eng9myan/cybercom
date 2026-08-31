from django.db import models

from platform.common.models import BaseModel
from products.cycom.accounting.models import Account, JournalEntry
from products.cycom.hr.models import Contract, Employee


class AttendanceRecord(BaseModel):
    """
    One clock-in/clock-out record for a given employee/date. `source` lets
    manual entries and imported device punches coexist — the biometric
    integration is a generic import endpoint (AttendanceViewSet.import_records),
    not a driver for a specific vendor's hardware.
    """

    SOURCE_CHOICES = [
        ("manual", "Manual"),
        ("biometric_import", "Biometric Import"),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="attendance")
    date = models.DateField()
    check_in = models.TimeField()
    check_out = models.TimeField()
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default="manual")

    # Rule engine inputs, computed on save() from check_in/check_out against
    # the employee's active contract's standard daily hours (standard_monthly_hours / 26).
    late_minutes = models.PositiveIntegerField(default=0)
    overtime_minutes = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "cycom_payroll_attendance"
        unique_together = [("tenant_id", "employee", "date")]
        ordering = ["-date"]

    def compute_minutes(self, standard_start_hour=9, standard_daily_hours=8):
        """
        Lateness = minutes after standard_start_hour. Overtime = minutes worked
        beyond standard_daily_hours. Both floored at 0 (early arrival/early
        leave isn't negative lateness/overtime in this rule set).
        """
        from datetime import datetime, timedelta

        base_date = datetime(2000, 1, 1)
        check_in_dt = base_date + timedelta(hours=self.check_in.hour, minutes=self.check_in.minute)
        check_out_dt = base_date + timedelta(hours=self.check_out.hour, minutes=self.check_out.minute)
        standard_start_dt = base_date + timedelta(hours=standard_start_hour)

        late = max(0, int((check_in_dt - standard_start_dt).total_seconds() // 60))
        worked_minutes = max(0, int((check_out_dt - check_in_dt).total_seconds() // 60))
        overtime = max(0, worked_minutes - standard_daily_hours * 60)

        self.late_minutes = late
        self.overtime_minutes = overtime

    def save(self, *args, **kwargs):
        self.compute_minutes()
        super().save(*args, **kwargs)


class PayrollRun(BaseModel):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("posted", "Posted"),
    ]

    period_start = models.DateField()
    period_end = models.DateField()
    currency = models.CharField(max_length=10, default="JOD")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")

    # GL config for this run — one consolidated journal entry per run rather
    # than one per payslip, matching how payroll is posted in practice.
    salary_expense_account = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name="payroll_runs_expense"
    )
    salary_payable_account = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name="payroll_runs_payable"
    )
    deduction_recovery_account = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name="payroll_runs_deduction", null=True, blank=True
    )

    journal_entry = models.ForeignKey(
        JournalEntry, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )

    class Meta:
        db_table = "cycom_payroll_runs"
        ordering = ["-period_start"]

    def __str__(self):
        return f"Payroll {self.period_start} – {self.period_end} ({self.status})"


class Payslip(BaseModel):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("posted", "Posted"),
    ]

    payroll_run = models.ForeignKey(PayrollRun, on_delete=models.CASCADE, related_name="payslips")
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name="payslips")
    contract = models.ForeignKey(Contract, on_delete=models.PROTECT, related_name="payslips")

    base_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    allowances_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    overtime_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    late_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    # Statutory deductions (Jordan): employee SS is withheld from net; employer
    # SS is a company cost tracked for the GL, not deducted from the employee.
    social_security_employee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    social_security_employer = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    income_tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gross_pay = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_pay = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")

    class Meta:
        db_table = "cycom_payroll_payslips"
        unique_together = [("payroll_run", "employee")]
        ordering = ["employee__employee_number"]

    def __str__(self):
        return f"Payslip {self.employee} — {self.payroll_run}"
