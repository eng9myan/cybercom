from django.db import models

from platform.common.models import BaseModel


class Account(BaseModel):
    """Chart of accounts entry."""

    ACCOUNT_TYPES = [
        ("asset", "Asset"),
        ("liability", "Liability"),
        ("equity", "Equity"),
        ("income", "Income"),
        ("expense", "Expense"),
    ]

    code = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    parent = models.ForeignKey(
        "self", on_delete=models.PROTECT, null=True, blank=True, related_name="children"
    )
    currency = models.CharField(max_length=10, default="JOD")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cycom_accounting_accounts"
        unique_together = [("tenant_id", "code")]
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} — {self.name}"


class JournalEntry(BaseModel):
    """Header for a double-entry accounting transaction."""

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("posted", "Posted"),
    ]

    date = models.DateField()
    reference = models.CharField(max_length=100, blank=True)
    currency = models.CharField(max_length=10, default="JOD")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    created_by = models.CharField(max_length=255, blank=True)
    narration = models.TextField(blank=True)

    class Meta:
        db_table = "cycom_accounting_journal_entries"
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.reference or self.id} ({self.status})"


class JournalLine(BaseModel):
    """Single debit/credit line of a journal entry."""

    entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name="lines")
    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="journal_lines")
    debit = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default="JOD")
    exchange_rate = models.DecimalField(max_digits=12, decimal_places=6, default=1)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cycom_accounting_journal_lines"
        ordering = ["id"]
