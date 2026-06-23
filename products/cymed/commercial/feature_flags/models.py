from django.db import models
from platform.common.models import BaseModel


class FeatureFlag(BaseModel):
    """Global feature flag definition."""
    FLAG_SCOPES = [
        ("global", "Global"),
        ("edition", "Edition-Based"),
        ("country", "Country-Based"),
        ("customer", "Customer-Based"),
        ("beta", "Beta"),
        ("government", "Government"),
    ]

    code = models.CharField(max_length=200, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    scope = models.CharField(max_length=50, choices=FLAG_SCOPES, default="edition")
    default_enabled = models.BooleanField(default=False)
    module_code = models.CharField(max_length=200, blank=True)  # owning module

    class Meta:
        db_table = "cymed_commercial_feature_flags"

    def __str__(self):
        return self.code


class FeatureDependency(BaseModel):
    """Feature X requires Feature Y to be enabled."""
    feature = models.ForeignKey(FeatureFlag, on_delete=models.CASCADE, related_name="dependencies")
    requires_feature_code = models.CharField(max_length=200)

    class Meta:
        db_table = "cymed_commercial_feature_dependencies"
        unique_together = [("feature", "requires_feature_code")]


class TenantFeature(BaseModel):
    """Per-tenant feature flag override — inherits from edition, overridable per customer."""
    feature = models.ForeignKey(FeatureFlag, on_delete=models.CASCADE, related_name="tenant_overrides")
    is_enabled = models.BooleanField(default=False)
    limit_override = models.PositiveIntegerField(null=True, blank=True)
    override_reason = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cymed_commercial_tenant_features"
        unique_together = [("tenant_id", "feature")]


class CustomerFeature(BaseModel):
    """Per-customer (cross-tenant) feature flag override — set by CyMed operations."""
    customer_id = models.UUIDField()
    feature = models.ForeignKey(FeatureFlag, on_delete=models.CASCADE, related_name="customer_overrides")
    is_enabled = models.BooleanField(default=False)
    enabled_by = models.UUIDField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_commercial_customer_features"
        unique_together = [("customer_id", "feature")]
