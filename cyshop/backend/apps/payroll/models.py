from django.db import models
from django.db.models import Sum

from apps.tenants.models import generate_uuid7, Tenant
from apps.hr.models import Employee


class PayrollBatch(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('processing', 'Processing'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
    ]

    id = models.UUIDField(primary_key=True, default=generate_uuid7, editable=False)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name='payroll_batches'
    )
    name = models.CharField(max_length=100)
    period_start = models.DateField()
    period_end = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    total_gross = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_net = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def update_totals(self):
        """Recompute total_gross and total_net by aggregating all payslips in this batch."""
        result = self.payslips.aggregate(
            total_gross=Sum('gross_salary'),
            total_net=Sum('net_salary'),
        )
        self.total_gross = result['total_gross'] or 0
        self.total_net = result['total_net'] or 0

    def __str__(self):
        return f"{self.name} ({self.period_start} - {self.period_end})"


class Payslip(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
    ]

    id = models.UUIDField(primary_key=True, default=generate_uuid7, editable=False)
    batch = models.ForeignKey(
        PayrollBatch, on_delete=models.CASCADE, related_name='payslips'
    )
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name='payslips'
    )
    gross_salary = models.DecimalField(max_digits=12, decimal_places=2)
    allowances_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    deductions_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    working_days = models.IntegerField(default=22)
    absent_days = models.IntegerField(default=0)
    overtime_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)

    def compute_net(self):
        """net_salary = gross_salary + allowances_total - deductions_total."""
        self.net_salary = self.gross_salary + self.allowances_total - self.deductions_total

    def save(self, *args, **kwargs):
        self.compute_net()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Payslip {self.employee} - {self.batch}"


class PayslipLine(models.Model):
    LINE_TYPE_CHOICES = [
        ('earning', 'Earning'),
        ('deduction', 'Deduction'),
    ]

    id = models.UUIDField(primary_key=True, default=generate_uuid7, editable=False)
    payslip = models.ForeignKey(
        Payslip, on_delete=models.CASCADE, related_name='lines'
    )
    line_type = models.CharField(max_length=20, choices=LINE_TYPE_CHOICES)
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.code} - {self.name}: {self.amount}"
