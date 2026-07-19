from django.db import models

from platform.common.models import BaseModel


class Expense(BaseModel):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("submitted", "Submitted"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("posted", "Posted"),
    ]

    employee_name = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=10, default="JOD")
    expense_date = models.DateField()
    description = models.TextField(blank=True)
    receipt = models.FileField(upload_to="cycom_expense_receipts/%Y/%m/", null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    approved_by = models.CharField(max_length=255, blank=True)
    rejection_reason = models.TextField(blank=True)
    expense_account = models.ForeignKey(
        "cycom_accounting.Account",
        on_delete=models.PROTECT,
        related_name="expenses",
        help_text="GL expense account debited when this expense is posted.",
    )
    payable_account = models.ForeignKey(
        "cycom_accounting.Account",
        on_delete=models.PROTECT,
        related_name="expense_payables",
        help_text="GL liability/cash account credited when this expense is posted.",
    )
    journal_entry = models.ForeignKey(
        "cycom_accounting.JournalEntry",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )

    class Meta:
        db_table = "cycom_expenses"
        ordering = ["-expense_date"]

    def __str__(self):
        return f"{self.employee_name} — {self.amount} {self.currency} ({self.status})"
