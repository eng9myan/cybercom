from django.db import models
from platform.common.models import BaseModel


class ProductCatalogEntry(BaseModel):
    """Master product registry for all CyMed products."""
    code = models.CharField(max_length=100, unique=True)    # "cymed_clinic", "cymed_hospital" etc.
    name = models.CharField(max_length=255)
    short_description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    current_version = models.CharField(max_length=50, default="1.0.0")

    class Meta:
        db_table = "cymed_commercial_product_catalog"

    def __str__(self):
        return f"{self.code} ({self.current_version})"


class ProductEdition(BaseModel):
    """An edition/tier of a product (e.g. Clinic Starter, Hospital Enterprise)."""
    EDITION_TIERS = [
        ("starter", "Starter"),
        ("professional", "Professional"),
        ("enterprise", "Enterprise"),
        ("community", "Community Hospital"),
        ("enterprise_hospital", "Enterprise Hospital"),
        ("medical_city", "Medical City"),
        ("basic", "Basic"),
        ("advanced", "Advanced"),
        ("reference_lab", "Reference Lab"),
        ("retail", "Retail"),
        ("chain", "Chain"),
        ("hospital_pharmacy", "Hospital Pharmacy"),
        ("standard", "Standard"),
        ("government", "Government"),
    ]

    product = models.ForeignKey(ProductCatalogEntry, on_delete=models.CASCADE, related_name="editions")
    code = models.CharField(max_length=100)
    name = models.CharField(max_length=255)
    tier = models.CharField(max_length=100, choices=EDITION_TIERS)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    # Limits
    max_users = models.PositiveIntegerField(default=0)       # 0 = unlimited
    max_providers = models.PositiveIntegerField(default=0)
    max_beds = models.PositiveIntegerField(default=0)        # hospital-specific
    max_facilities = models.PositiveIntegerField(default=0)
    max_clinics = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "cymed_commercial_product_editions"
        unique_together = [("product", "code")]

    def __str__(self):
        return f"{self.product.code}:{self.code}"


class EditionFeature(BaseModel):
    """Feature entitlements for a product edition."""
    edition = models.ForeignKey(ProductEdition, on_delete=models.CASCADE, related_name="features")
    feature_code = models.CharField(max_length=200)
    is_enabled = models.BooleanField(default=True)
    limit_value = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        db_table = "cymed_commercial_edition_features"
        unique_together = [("edition", "feature_code")]


class EditionLimit(BaseModel):
    """Named resource limits for a product edition."""
    edition = models.ForeignKey(ProductEdition, on_delete=models.CASCADE, related_name="limits")
    resource_name = models.CharField(max_length=100)    # "beds", "users", "api_calls"
    max_value = models.PositiveIntegerField(default=0)  # 0 = unlimited
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cymed_commercial_edition_limits"
        unique_together = [("edition", "resource_name")]


class EditionModule(BaseModel):
    """Maps a module to a product edition."""
    edition = models.ForeignKey(ProductEdition, on_delete=models.CASCADE, related_name="modules")
    module_code = models.CharField(max_length=200)      # e.g. "clinic.appointments", "hospital.icu"
    is_included = models.BooleanField(default=True)

    class Meta:
        db_table = "cymed_commercial_edition_modules"
        unique_together = [("edition", "module_code")]
