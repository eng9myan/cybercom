from django.db import models
from platform.common.models import BaseModel


class AssetCategory(BaseModel):
    DEPRECIATION_METHOD_CHOICES = [
        ("straight_line", "Straight Line"),
        ("declining_balance", "Declining Balance"),
    ]

    code = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    useful_life_years = models.IntegerField(default=5)
    depreciation_method = models.CharField(
        max_length=20,
        choices=DEPRECIATION_METHOD_CHOICES,
        default="straight_line",
    )
    salvage_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        db_table = "cycom_assets_fixed_asset_categories"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} — {self.name}"


class FixedAsset(BaseModel):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("disposed", "Disposed"),
        ("under_maintenance", "Under Maintenance"),
        ("written_off", "Written Off"),
    ]

    asset_number = models.CharField(max_length=50)
    name = models.CharField(max_length=200)
    name_ar = models.CharField(max_length=200, blank=True)
    category = models.ForeignKey(AssetCategory, on_delete=models.PROTECT, related_name="assets")
    acquisition_date = models.DateField()
    acquisition_cost = models.DecimalField(max_digits=18, decimal_places=2)
    current_book_value = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    depreciation_accumulated = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    location = models.CharField(max_length=200, blank=True)
    assigned_to = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = "cycom_assets_fixed_assets"
        ordering = ["asset_number"]

    def __str__(self):
        return f"{self.asset_number} — {self.name}"


class Depreciation(BaseModel):
    asset = models.ForeignKey(FixedAsset, on_delete=models.CASCADE, related_name="depreciations")
    period_year = models.IntegerField()
    period_month = models.IntegerField()
    depreciation_amount = models.DecimalField(max_digits=18, decimal_places=2)
    book_value_after = models.DecimalField(max_digits=18, decimal_places=2)
    posted = models.BooleanField(default=False)

    class Meta:
        db_table = "cycom_assets_depreciations"
        ordering = ["period_year", "period_month"]

    def __str__(self):
        return f"Dep {self.asset.asset_number} {self.period_year}/{self.period_month:02d}"
