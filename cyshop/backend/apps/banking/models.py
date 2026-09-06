"""
Bank accounts, imported statements, and reconciliation against the books.

    BankAccount            a cash/bank account, optionally tied to a GL account
    BankStatement          one imported statement (a period of lines)
    BankStatementLine      a single bank transaction (signed amount)
    ReconciliationSession  a reconcile run: book balance vs statement balance,
                           the line-by-line matches, and whether it ties out
"""
from decimal import Decimal

from django.db import models

from apps.tenants.models import BaseEntity, Company

Z2 = Decimal("0.01")


class BankAccount(BaseEntity):
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="bank_accounts")
    name = models.CharField(max_length=120)
    bank_name = models.CharField(max_length=120, blank=True)
    account_number = models.CharField(max_length=64, blank=True)
    iban = models.CharField(max_length=40, blank=True)
    currency = models.CharField(max_length=3, default="SAR")
    gl_account_id = models.UUIDField(null=True, blank=True)   # accounting.Account
    opening_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "banking_accounts"
        unique_together = [("tenant_id", "company", "name")]
        ordering = ["name"]

    @property
    def book_balance(self) -> Decimal:
        agg = self.statement_lines.filter(is_deleted=False, reconciled=True).aggregate(
            s=models.Sum("amount"))
        return (Decimal(self.opening_balance) + (agg["s"] or Decimal("0"))).quantize(Z2)

    def __str__(self):
        return f"{self.name} ({self.currency})"


class BankStatement(BaseEntity):
    bank_account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name="statements")
    reference = models.CharField(max_length=80, blank=True)
    statement_date = models.DateField()
    opening_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    closing_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    line_count = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "banking_statements"
        ordering = ["-statement_date"]


class BankStatementLine(BaseEntity):
    bank_account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name="statement_lines")
    statement = models.ForeignKey(BankStatement, on_delete=models.CASCADE, related_name="lines",
                                  null=True, blank=True)
    txn_date = models.DateField()
    description = models.CharField(max_length=255)
    reference = models.CharField(max_length=120, blank=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2,
                                 help_text="Signed: positive = money in, negative = money out")

    matched = models.BooleanField(default=False)
    match_type = models.CharField(max_length=24, blank=True)   # pos_payment | journal_line | manual
    match_id = models.UUIDField(null=True, blank=True)
    match_note = models.CharField(max_length=255, blank=True)
    reconciled = models.BooleanField(default=False)

    class Meta:
        db_table = "banking_statement_lines"
        ordering = ["txn_date", "created_at"]


class ReconciliationSession(BaseEntity):
    STATUS = [("in_progress", "In progress"), ("completed", "Completed")]

    bank_account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name="reconciliations")
    period_start = models.DateField()
    period_end = models.DateField()
    statement_closing_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    book_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    difference = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    status = models.CharField(max_length=12, choices=STATUS, default="in_progress")
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "banking_reconciliation_sessions"
        ordering = ["-period_end"]
