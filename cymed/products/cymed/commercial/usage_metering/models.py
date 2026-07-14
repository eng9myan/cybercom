from django.db import models

from platform.common.models import BaseModel


class UsageMeter(BaseModel):
    """Daily per-tenant usage snapshot for billing and compliance."""

    snapshot_date = models.DateField()
    product_code = models.CharField(max_length=100)
    edition_code = models.CharField(max_length=100, blank=True)

    # Users
    active_users = models.PositiveIntegerField(default=0)
    active_providers = models.PositiveIntegerField(default=0)

    # Facilities
    active_facilities = models.PositiveIntegerField(default=0)
    active_clinics = models.PositiveIntegerField(default=0)
    active_hospitals = models.PositiveIntegerField(default=0)
    licensed_beds = models.PositiveIntegerField(default=0)
    occupied_beds = models.PositiveIntegerField(default=0)

    # Platform
    api_calls = models.PositiveBigIntegerField(default=0)
    storage_gb = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    total_transactions = models.PositiveBigIntegerField(default=0)

    # Alerts
    is_over_user_limit = models.BooleanField(default=False)
    is_over_bed_limit = models.BooleanField(default=False)
    is_over_api_limit = models.BooleanField(default=False)

    class Meta:
        db_table = "cymed_commercial_usage_meters"
        unique_together = [("tenant_id", "snapshot_date", "product_code")]


class UsageAlert(BaseModel):
    """Alert generated when usage approaches or exceeds limits."""

    SEVERITY_LEVELS = [
        ("info", "Info"),
        ("warning", "Warning"),
        ("critical", "Critical"),
    ]
    ALERT_TYPES = [
        ("approaching_limit", "Approaching Limit"),
        ("over_limit", "Over Limit"),
        ("license_expiry", "License Expiry"),
        ("api_quota", "API Quota"),
    ]

    meter = models.ForeignKey(UsageMeter, on_delete=models.CASCADE, related_name="alerts")
    alert_type = models.CharField(max_length=50, choices=ALERT_TYPES)
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS, default="warning")
    resource = models.CharField(max_length=100)  # "users", "beds", "api_calls"
    current_value = models.PositiveIntegerField()
    limit_value = models.PositiveIntegerField()
    percentage_used = models.DecimalField(max_digits=5, decimal_places=2)
    is_resolved = models.BooleanField(default=False)

    class Meta:
        db_table = "cymed_commercial_usage_alerts"
