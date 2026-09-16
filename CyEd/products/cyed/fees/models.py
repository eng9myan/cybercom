from decimal import Decimal

from django.db import models
from django.db.models import Sum

from platform.common.models import BaseModel
from products.cyed.sis.models import AcademicYear, Student


class FeeSchedule(BaseModel):
    FREQUENCY_CHOICES = [
        ("annual", "Annual"),
        ("semester", "Per Semester"),
        ("term", "Per Term"),
        ("once", "One-off"),
    ]

    name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default="AUD")
    academic_year = models.ForeignKey(
        AcademicYear, on_delete=models.SET_NULL, null=True, blank=True, related_name="fee_schedules"
    )
    applies_to_year_level = models.PositiveSmallIntegerField(null=True, blank=True)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default="annual")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cyed_fee_schedules"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.amount} {self.currency})"


class Invoice(BaseModel):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("issued", "Issued"),
        ("paid", "Paid"),
        ("partial", "Partially Paid"),
        ("overdue", "Overdue"),
        ("cancelled", "Cancelled"),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="invoices")
    fee_schedule = models.ForeignKey(
        FeeSchedule, on_delete=models.SET_NULL, null=True, blank=True, related_name="invoices"
    )
    description = models.CharField(max_length=255, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default="AUD")
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    issued_on = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "cyed_invoices"
        ordering = ["-created_at"]

    @property
    def paid_total(self) -> Decimal:
        return self.payments.aggregate(t=Sum("amount"))["t"] or Decimal("0")

    @property
    def balance(self) -> Decimal:
        return Decimal(self.amount) - self.paid_total

    def recalc_status(self):
        if self.status == "cancelled":
            return
        paid = self.paid_total
        if paid <= 0:
            self.status = "issued" if self.issued_on else "draft"
        elif paid < Decimal(self.amount):
            self.status = "partial"
        else:
            self.status = "paid"
        self.save(update_fields=["status", "updated_at"])

    def __str__(self):
        return f"Invoice {self.student_id} {self.amount} ({self.status})"


class Payment(BaseModel):
    METHOD_CHOICES = [
        ("card", "Card"),
        ("bank_transfer", "Bank Transfer"),
        ("bpay", "BPAY"),
        ("direct_debit", "Direct Debit"),
        ("cash", "Cash"),
    ]

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default="card")
    paid_on = models.DateField(null=True, blank=True)
    reference = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "cyed_payments"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Payment {self.amount} on {self.invoice_id}"
