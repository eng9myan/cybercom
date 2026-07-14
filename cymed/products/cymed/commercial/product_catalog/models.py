from django.db import models

from platform.common.models import BaseModel


class ProductVersion(BaseModel):
    """Version history for a product in the catalog."""

    product_code = models.CharField(max_length=100)
    version = models.CharField(max_length=50)
    release_date = models.DateField()
    release_notes = models.TextField(blank=True)
    is_lts = models.BooleanField(default=False)
    minimum_upgrade_from = models.CharField(max_length=50, blank=True)

    class Meta:
        db_table = "cymed_commercial_product_versions"
        unique_together = [("product_code", "version")]


class ProductLicenseMapping(BaseModel):
    """Maps a product+edition to licensing rules and capabilities."""

    product_code = models.CharField(max_length=100)
    edition_code = models.CharField(max_length=100)
    license_types_allowed = models.JSONField(default=list)
    delivery_modes_allowed = models.JSONField(default=list)
    supports_white_label = models.BooleanField(default=True)
    supports_multi_tenant = models.BooleanField(default=False)
    requires_government_license = models.BooleanField(default=False)

    class Meta:
        db_table = "cymed_commercial_product_license_mappings"
        unique_together = [("product_code", "edition_code")]


class ProductFeatureMatrix(BaseModel):
    """Cross-product feature availability matrix."""

    product_code = models.CharField(max_length=100)
    edition_code = models.CharField(max_length=100)
    feature_code = models.CharField(max_length=200)
    is_available = models.BooleanField(default=True)
    requires_addon = models.BooleanField(default=False)
    addon_code = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "cymed_commercial_product_feature_matrix"
        unique_together = [("product_code", "edition_code", "feature_code")]
