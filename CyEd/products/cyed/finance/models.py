from decimal import Decimal

from django.db import models

from platform.common.models import BaseModel


class Account(BaseModel):
    TYPES = [("asset", "Asset"), ("liability", "Liability"), ("equity", "Equity"),
             ("income", "Income"), ("expense", "Expense")]

    code = models.CharField(max_length=20)
    name = models.CharField(max_length=255)
    account_type = models.CharField(max_length=20, choices=TYPES)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cyed_finance_accounts"
        ordering = ["code"]
        constraints = [models.UniqueConstraint(fields=["tenant_id", "code"], name="uniq_account_code")]

    def __str__(self):
        return f"{self.code} {self.name}"


class JournalEntry(BaseModel):
    date = models.DateField(null=True, blank=True)
    reference = models.CharField(max_length=100, blank=True)
    narration = models.CharField(max_length=255, blank=True)
    posted = models.BooleanField(default=False)

    class Meta:
        db_table = "cyed_finance_journal_entries"
        ordering = ["-date", "-created_at"]

    @property
    def total_debit(self) -> Decimal:
        return sum((line.debit for line in self.lines.all()), Decimal("0"))

    @property
    def total_credit(self) -> Decimal:
        return sum((line.credit for line in self.lines.all()), Decimal("0"))

    @property
    def is_balanced(self) -> bool:
        return self.total_debit == self.total_credit and self.total_debit > 0

    def __str__(self):
        return f"JE {self.reference or self.id} ({'posted' if self.posted else 'draft'})"


class JournalLine(BaseModel):
    entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name="lines")
    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="lines")
    debit = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cyed_finance_journal_lines"
        ordering = ["id"]

    def __str__(self):
        return f"{self.account_id} Dr {self.debit} Cr {self.credit}"


class Budget(BaseModel):
    """An annual budget cycle. Actuals are read live from posted GL entries."""

    STATUS = [("draft", "Draft"), ("approved", "Approved"), ("closed", "Closed")]

    name = models.CharField(max_length=255)
    fiscal_year = models.CharField(max_length=20)  # e.g. "2026"
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default="draft")
    approved_by = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cyed_finance_budgets"
        ordering = ["-fiscal_year"]
        constraints = [
            models.UniqueConstraint(fields=["tenant_id", "fiscal_year", "name"], name="uniq_budget_per_year")
        ]

    def __str__(self):
        return f"{self.name} {self.fiscal_year} ({self.status})"


class BudgetLine(BaseModel):
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name="lines")
    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="budget_lines")
    budgeted_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cyed_finance_budget_lines"
        ordering = ["account__code"]
        constraints = [
            models.UniqueConstraint(fields=["budget", "account"], name="uniq_budget_line_per_account")
        ]

    def actual(self) -> Decimal:
        """Actual movement on this account within the budget period."""
        lines = self.account.lines.filter(entry__posted=True)
        if self.budget.start_date:
            lines = lines.filter(entry__date__gte=self.budget.start_date)
        if self.budget.end_date:
            lines = lines.filter(entry__date__lte=self.budget.end_date)
        dr = sum((l.debit for l in lines), Decimal("0"))
        cr = sum((l.credit for l in lines), Decimal("0"))
        # Expenses/assets increase on the debit side; income/liabilities on credit.
        return dr - cr if self.account.account_type in ("expense", "asset") else cr - dr

    def variance(self) -> Decimal:
        return Decimal(self.budgeted_amount) - self.actual()

    def __str__(self):
        return f"{self.account_id} budget {self.budgeted_amount}"


class BankStatement(BaseModel):
    """
    One imported bank statement covering a period for a single bank account.

    Reconciliation is a *period* activity, not a per-line one: an accountant
    reconciles March, proves the closing balance, and locks it. Holding the
    opening/closing balance here is what lets the system say "this period
    reconciles" rather than merely "these lines are ticked".
    """

    STATUS = [("open", "Open"), ("reconciled", "Reconciled"), ("locked", "Locked")]

    account = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name="bank_statements",
        help_text="The GL cash/bank account this statement belongs to.",
    )
    reference = models.CharField(max_length=100, blank=True)
    period_start = models.DateField()
    period_end = models.DateField()
    opening_balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    closing_balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    source_filename = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default="open")
    imported_by = models.CharField(max_length=255, blank=True)
    reconciled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cyed_finance_bank_statements"
        ordering = ["-period_end", "-created_at"]

    @property
    def line_total(self) -> Decimal:
        return self.lines.aggregate(t=models.Sum("amount"))["t"] or Decimal("0")

    @property
    def expected_closing(self) -> Decimal:
        """Opening balance plus every line on the statement."""
        return Decimal(self.opening_balance) + self.line_total

    @property
    def balances(self) -> bool:
        """Does the statement internally add up? Catches a truncated import."""
        return self.expected_closing == Decimal(self.closing_balance)

    @property
    def unreconciled_count(self) -> int:
        return self.lines.filter(is_reconciled=False).count()

    @property
    def is_fully_reconciled(self) -> bool:
        return self.lines.exists() and self.unreconciled_count == 0

    def __str__(self):
        return f"Statement {self.reference or self.id} {self.period_start}..{self.period_end}"


class BankStatementLine(BaseModel):
    """
    A line imported from a bank statement, matched against the ledger during
    reconciliation. `amount` is signed: positive = money in, negative = money out.
    """

    statement = models.ForeignKey(
        BankStatement, on_delete=models.CASCADE, null=True, blank=True, related_name="lines"
    )
    date = models.DateField()
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    bank_reference = models.CharField(max_length=100, blank=True)
    is_reconciled = models.BooleanField(default=False)
    matched_entry = models.ForeignKey(
        JournalEntry, on_delete=models.SET_NULL, null=True, blank=True, related_name="bank_lines"
    )
    reconciled_at = models.DateTimeField(null=True, blank=True)
    reconciled_by = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cyed_finance_bank_statement_lines"
        ordering = ["-date", "-created_at"]
        indexes = [models.Index(fields=["tenant_id", "is_reconciled"], name="idx_bankline_reconciled")]

    def __str__(self):
        return f"{self.date} {self.description} {self.amount}"
