from django.db import models

from platform.common.models import BaseModel


class Asset(BaseModel):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("retired", "Retired"),
        ("maintenance", "Maintenance"),
    ]

    name = models.CharField(max_length=200)
    code = models.CharField(max_length=100)
    asset_type = models.CharField(max_length=50)  # e.g., medical_device, computer, vehicle
    purchase_date = models.DateField()
    purchase_cost = models.DecimalField(max_digits=18, decimal_places=2)
    salvage_value = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    useful_life_years = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")

    class Meta:
        db_table = "cycom_assets"

    def __str__(self):
        return f"{self.code} - {self.name}"


class AssetDepreciation(BaseModel):
    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name="depreciations",
    )
    depreciation_date = models.DateField()
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    accumulated_depreciation = models.DecimalField(max_digits=18, decimal_places=2)
    book_value = models.DecimalField(max_digits=18, decimal_places=2)

    class Meta:
        db_table = "cycom_asset_depreciations"
        ordering = ["-depreciation_date"]
