import calendar as _calendar

from django.db import models
from django.utils import timezone

from platform.common.models import BaseModel
from products.cycom.accounting.models import Account
from products.cycom.ar_ap.models import Partner


class SubscriptionPlan(BaseModel):
    INTERVAL_CHOICES = [
        ("monthly", "Monthly"),
        ("quarterly", "Quarterly"),
        ("yearly", "Yearly"),
    ]

    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=10, default="JOD")
    billing_interval = models.CharField(max_length=10, choices=INTERVAL_CHOICES, default="monthly")
    revenue_account = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name="subscription_plans"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cycom_subscription_plans"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.price} {self.currency}/{self.billing_interval})"

    def next_date_after(self, from_date):
        months_to_add = {"monthly": 1, "quarterly": 3, "yearly": 12}[self.billing_interval]
        total_months = from_date.month - 1 + months_to_add
        year = from_date.year + total_months // 12
        month = total_months % 12 + 1
        day = min(from_date.day, _calendar.monthrange(year, month)[1])
        return from_date.replace(year=year, month=month, day=day)


class Subscription(BaseModel):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("paused", "Paused"),
        ("cancelled", "Cancelled"),
    ]

    customer = models.ForeignKey(Partner, on_delete=models.PROTECT, related_name="subscriptions")
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, related_name="subscriptions")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="active")
    start_date = models.DateField(default=timezone.now)
    next_billing_date = models.DateField()
    control_account = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name="subscription_receivables",
        help_text="Accounts Receivable control account used on generated invoices.",
    )
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cycom_subscriptions"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.customer} — {self.plan} ({self.status})"
