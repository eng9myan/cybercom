from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from apps.tenants.models import BaseEntity


class Account(BaseEntity):
    """Chart-of-Accounts node. Supports a tree via the parent FK."""

    ACCOUNT_TYPES = [
        ('asset', 'Asset'),
        ('liability', 'Liability'),
        ('equity', 'Equity'),
        ('revenue', 'Revenue'),
        ('expense', 'Expense'),
    ]

    code = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    name_ar = models.CharField(max_length=200)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
    )

    class Meta:
        ordering = ['code']
        unique_together = [('tenant_id', 'code')]

    def __str__(self):
        return f"{self.code} – {self.name}"


class Journal(BaseEntity):
    """A named journal that groups related entries (e.g. Sales Journal, Cash Journal)."""

    JOURNAL_TYPES = [
        ('general', 'General'),
        ('sales', 'Sales'),
        ('purchase', 'Purchase'),
        ('cash', 'Cash'),
        ('bank', 'Bank'),
    ]

    code = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    journal_type = models.CharField(max_length=20, choices=JOURNAL_TYPES)
    currency = models.CharField(max_length=3, default='SAR')

    class Meta:
        ordering = ['code']
        unique_together = [('tenant_id', 'code')]

    def __str__(self):
        return f"{self.code} – {self.name}"


class JournalEntry(BaseEntity):
    """Header record for a double-entry accounting transaction."""

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancelled', 'Cancelled'),
    ]

    journal = models.ForeignKey(Journal, on_delete=models.CASCADE, related_name='entries')
    reference = models.CharField(max_length=100)
    entry_date = models.DateField()
    description = models.CharField(max_length=500)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    class Meta:
        ordering = ['-entry_date', '-created_at']

    @property
    def is_balanced(self):
        """Return True when total debits equal total credits across all lines."""
        from django.db.models import Sum
        totals = self.lines.aggregate(
            total_debit=Sum('debit'),
            total_credit=Sum('credit'),
        )
        debit = totals['total_debit'] or 0
        credit = totals['total_credit'] or 0
        return debit == credit

    def clean(self):
        """Prevent posting an unbalanced entry."""
        if self.status == 'posted' and not self.is_balanced:
            raise ValidationError(
                'Journal entry cannot be posted: total debits do not equal total credits.'
            )

    def __str__(self):
        return f"{self.reference} ({self.entry_date}) [{self.status}]"


class JournalEntryLine(BaseEntity):
    """A single debit or credit line within a JournalEntry."""

    entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='lines')
    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='entry_lines')
    description = models.CharField(max_length=300, blank=True)
    debit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    line_order = models.IntegerField(default=0)

    class Meta:
        ordering = ['line_order', 'id']

    def __str__(self):
        return f"Line {self.line_order}: Dr {self.debit} / Cr {self.credit} [{self.account.code}]"


class FiscalPeriod(BaseEntity):
    """An accounting period (month/quarter/year) that can be opened or closed."""

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('closed', 'Closed'),
    ]

    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.name} ({self.start_date} → {self.end_date}) [{self.status}]"
