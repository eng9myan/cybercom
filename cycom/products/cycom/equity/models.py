from decimal import Decimal

from django.db import models

from platform.common.models import BaseModel


class ShareClass(BaseModel):
    """
    A single class of stock. Common has no liquidation preference
    (multiple=0). Preferred classes are paid out in seniority order
    (lowest seniority_rank first) before anything reaches common.

    convert_to_common is a MANUAL election, not an automatic optimization:
    whether converting to common beats taking the liquidation preference
    depends on what every other class does too (a genuinely circular
    calculation in real waterfalls) — this models it as an explicit
    per-class decision instead of guessing, matching how real cap table
    tools and real shareholder elections work.
    """

    CLASS_TYPE_CHOICES = [("common", "Common"), ("preferred", "Preferred")]

    name = models.CharField(max_length=255)
    class_type = models.CharField(max_length=10, choices=CLASS_TYPE_CHOICES, default="common")
    liquidation_preference_multiple = models.DecimalField(
        max_digits=6, decimal_places=2, default=Decimal("0"),
        help_text="e.g. 1.00 for 1x, 2.00 for 2x. Always 0 for common.",
    )
    seniority_rank = models.PositiveIntegerField(
        default=100, help_text="Lower is paid first. Only meaningful for preferred classes."
    )
    is_participating = models.BooleanField(
        default=False,
        help_text="If true, this class takes its preference AND shares pro-rata in what's left.",
    )
    convert_to_common = models.BooleanField(
        default=False,
        help_text="Manual election: skip liquidation preference entirely, join the common pro-rata pool instead.",
    )
    conversion_ratio = models.DecimalField(
        max_digits=8, decimal_places=4, default=Decimal("1.0000"),
        help_text="How many common-equivalent shares each share of this class counts as when participating pro-rata.",
    )

    class Meta:
        db_table = "cycom_equity_share_classes"
        ordering = ["seniority_rank", "name"]

    def __str__(self):
        return self.name


class Shareholder(BaseModel):
    HOLDER_TYPE_CHOICES = [
        ("founder", "Founder"),
        ("employee", "Employee"),
        ("investor", "Investor"),
        ("other", "Other"),
    ]

    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True)
    holder_type = models.CharField(max_length=20, choices=HOLDER_TYPE_CHOICES, default="other")

    class Meta:
        db_table = "cycom_equity_shareholders"
        ordering = ["name"]

    def __str__(self):
        return self.name


class ShareGrant(BaseModel):
    """
    One issuance of shares. price_per_share is the original issue price
    (needed to compute liquidation preference — preference is always
    based on what was originally paid, not current value). Vesting is
    optional (vest_duration_months=0 means fully vested immediately,
    the normal case for investor rounds; founder/employee grants
    typically set a real cliff + vest duration).
    """

    shareholder = models.ForeignKey(Shareholder, on_delete=models.PROTECT, related_name="grants")
    share_class = models.ForeignKey(ShareClass, on_delete=models.PROTECT, related_name="grants")
    quantity = models.DecimalField(max_digits=16, decimal_places=4)
    price_per_share = models.DecimalField(max_digits=14, decimal_places=6)
    grant_date = models.DateField()
    vesting_start_date = models.DateField(null=True, blank=True)
    cliff_months = models.PositiveIntegerField(default=0)
    vest_duration_months = models.PositiveIntegerField(
        default=0, help_text="0 means fully vested immediately (no cliff/vesting schedule)."
    )
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cycom_equity_share_grants"
        ordering = ["grant_date"]

    def __str__(self):
        return f"{self.shareholder} — {self.quantity} {self.share_class}"

    def vested_quantity(self, as_of_date):
        if self.vest_duration_months == 0 or self.vesting_start_date is None:
            return self.quantity
        if as_of_date < self.vesting_start_date:
            return Decimal("0")

        months_elapsed = (
            (as_of_date.year - self.vesting_start_date.year) * 12
            + (as_of_date.month - self.vesting_start_date.month)
        )
        if as_of_date.day < self.vesting_start_date.day:
            months_elapsed -= 1
        months_elapsed = max(0, months_elapsed)

        if months_elapsed < self.cliff_months:
            return Decimal("0")
        if months_elapsed >= self.vest_duration_months:
            return self.quantity
        return (self.quantity * months_elapsed / self.vest_duration_months).quantize(Decimal("0.0001"))


class DividendDistribution(BaseModel):
    STATUS_CHOICES = [("draft", "Draft"), ("computed", "Computed"), ("paid", "Paid")]

    total_amount = models.DecimalField(max_digits=16, decimal_places=2)
    currency = models.CharField(max_length=10, default="JOD")
    distribution_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="draft")

    class Meta:
        db_table = "cycom_equity_dividend_distributions"
        ordering = ["-distribution_date"]

    def __str__(self):
        return f"Distribution {self.distribution_date} — {self.total_amount} {self.currency} ({self.status})"


class DividendAllocation(BaseModel):
    BASIS_CHOICES = [
        ("liquidation_preference", "Liquidation Preference"),
        ("pro_rata", "Pro-Rata Participation"),
    ]

    distribution = models.ForeignKey(DividendDistribution, on_delete=models.CASCADE, related_name="allocations")
    shareholder = models.ForeignKey(Shareholder, on_delete=models.PROTECT, related_name="dividend_allocations")
    grant = models.ForeignKey(ShareGrant, on_delete=models.PROTECT, related_name="dividend_allocations")
    amount = models.DecimalField(max_digits=16, decimal_places=2)
    basis = models.CharField(max_length=25, choices=BASIS_CHOICES)

    class Meta:
        db_table = "cycom_equity_dividend_allocations"
        ordering = ["shareholder__name"]
