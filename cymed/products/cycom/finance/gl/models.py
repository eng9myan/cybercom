from django.db import models

from platform.common.models import BaseModel


class Account(BaseModel):
    ACCOUNT_TYPE_CHOICES = [
        ("asset", "Asset"),
        ("liability", "Liability"),
        ("equity", "Equity"),
        ("revenue", "Revenue"),
        ("expense", "Expense"),
    ]

    code = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    name_ar = models.CharField(max_length=200, blank=True)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES)
    parent_account = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="children",
    )
    is_active = models.BooleanField(default=True)
    currency = models.CharField(max_length=3, default="SAR")
    balance = models.DecimalField(max_digits=18, decimal_places=2, default=0)

    class Meta:
        db_table = "cycom_finance_gl_accounts"

    def __str__(self):
        return f"{self.code} - {self.name}"


class JournalEntry(BaseModel):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("posted", "Posted"),
        ("reversed", "Reversed"),
    ]

    entry_date = models.DateField()
    description = models.TextField(blank=True)
    reference = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    posted_by = models.UUIDField(null=True, blank=True)
    posted_at = models.DateTimeField(null=True, blank=True)
    total_debit = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    total_credit = models.DecimalField(max_digits=18, decimal_places=2, default=0)

    class Meta:
        db_table = "cycom_finance_gl_journal_entries"

    def __str__(self):
        return f"JE-{self.id} ({self.entry_date})"


class JournalLine(BaseModel):
    journal = models.ForeignKey(
        JournalEntry,
        on_delete=models.CASCADE,
        related_name="lines",
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name="journal_lines",
    )
    debit = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    description = models.CharField(max_length=500, blank=True)
    cost_center = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "cycom_finance_gl_journal_lines"

    def __str__(self):
        return f"Line {self.id} - {self.account.code}"
