from django.db import models

from platform.common.models import BaseModel


class SubscriptionPlan(BaseModel):
    """Subscription plan definition (pricing + billing cycle)."""

    BILLING_CYCLES = [
        ("monthly", "Monthly"),
        ("quarterly", "Quarterly"),
        ("annual", "Annual"),
        ("multi_year", "Multi-Year"),
        ("enterprise", "Enterprise Agreement"),
    ]

    code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    product_code = models.CharField(max_length=100)
    edition_code = models.CharField(max_length=100)
    billing_cycle = models.CharField(max_length=50, choices=BILLING_CYCLES, default="annual")
    base_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default="USD")
    per_user_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    per_bed_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cymed_commercial_subscription_plans"

    def __str__(self):
        return f"{self.code} ({self.billing_cycle})"


class Subscription(BaseModel):
    """Active subscription for a customer/tenant."""

    STATUS_CHOICES = [
        ("trial", "Trial"),
        ("active", "Active"),
        ("past_due", "Past Due"),
        ("cancelled", "Cancelled"),
        ("expired", "Expired"),
        ("suspended", "Suspended"),
    ]

    plan = models.ForeignKey(
        SubscriptionPlan, on_delete=models.PROTECT, related_name="subscriptions"
    )
    customer_id = models.UUIDField()
    license_id = models.UUIDField(null=True, blank=True)

    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="active")
    started_at = models.DateField()
    current_period_start = models.DateField()
    current_period_end = models.DateField()
    auto_renew = models.BooleanField(default=True)
    contracted_users = models.PositiveIntegerField(default=0)
    contracted_beds = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "cymed_commercial_subscriptions"


class SubscriptionUsage(BaseModel):
    """Monthly usage snapshot for billing reconciliation."""

    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name="usage")
    period_start = models.DateField()
    period_end = models.DateField()
    peak_users = models.PositiveIntegerField(default=0)
    peak_providers = models.PositiveIntegerField(default=0)
    peak_beds = models.PositiveIntegerField(default=0)
    total_api_calls = models.PositiveBigIntegerField(default=0)
    total_storage_gb = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    total_transactions = models.PositiveBigIntegerField(default=0)
    billable_overage = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        db_table = "cymed_commercial_subscription_usage"
        unique_together = [("subscription", "period_start")]


class SubscriptionInvoice(BaseModel):
    """Invoice generated for a subscription period."""

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("issued", "Issued"),
        ("paid", "Paid"),
        ("overdue", "Overdue"),
        ("void", "Void"),
    ]

    subscription = models.ForeignKey(
        Subscription, on_delete=models.CASCADE, related_name="invoices"
    )
    invoice_number = models.CharField(max_length=100, unique=True)
    period_start = models.DateField()
    period_end = models.DateField()
    base_amount = models.DecimalField(max_digits=12, decimal_places=2)
    overage_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, default="USD")
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="draft")
    due_date = models.DateField()
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cymed_commercial_subscription_invoices"


class SubscriptionContract(BaseModel):
    """Enterprise agreement / multi-year contract."""

    subscription = models.OneToOneField(
        Subscription, on_delete=models.CASCADE, related_name="contract"
    )
    contract_number = models.CharField(max_length=100, unique=True)
    signed_at = models.DateField(null=True, blank=True)
    contract_years = models.PositiveIntegerField(default=1)
    total_contract_value = models.DecimalField(max_digits=15, decimal_places=2)
    payment_terms = models.CharField(max_length=255, blank=True)
    sla_tier = models.CharField(max_length=50, default="standard")  # standard, gold, platinum
    dedicated_csm = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_commercial_subscription_contracts"
