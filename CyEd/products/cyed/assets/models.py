from datetime import date
from decimal import Decimal

from django.db import models

from platform.common.models import BaseModel


class Asset(BaseModel):
    STATUS = [("in_use", "In Use"), ("maintenance", "Maintenance"), ("disposed", "Disposed")]

    name = models.CharField(max_length=255)
    asset_tag = models.CharField(max_length=50, blank=True)
    category = models.CharField(max_length=100, blank=True)  # ICT, furniture, vehicle...
    location = models.CharField(max_length=100, blank=True)
    acquisition_date = models.DateField(null=True, blank=True)
    acquisition_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    useful_life_years = models.PositiveSmallIntegerField(default=5)
    salvage_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS, default="in_use")

    class Meta:
        db_table = "cyed_assets"
        ordering = ["name"]

    def annual_depreciation(self) -> Decimal:
        life = self.useful_life_years or 1
        return ((Decimal(self.acquisition_cost) - Decimal(self.salvage_value)) / life).quantize(Decimal("0.01"))

    def book_value(self, as_of: date | None = None) -> Decimal:
        as_of = as_of or date.today()
        if not self.acquisition_date:
            return Decimal(self.acquisition_cost)
        years = max(0, (as_of - self.acquisition_date).days / 365.25)
        dep = min(Decimal(str(years)) * self.annual_depreciation(),
                  Decimal(self.acquisition_cost) - Decimal(self.salvage_value))
        return (Decimal(self.acquisition_cost) - dep).quantize(Decimal("0.01"))

    def __str__(self):
        return f"{self.name} ({self.status})"
