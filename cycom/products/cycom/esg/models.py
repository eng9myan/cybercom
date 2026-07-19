from decimal import Decimal

from django.db import models

from platform.common.models import BaseModel


class EmissionFactor(BaseModel):
    """
    kg CO2e per unit of activity. Seeded with commonly-cited reference
    values as a starting point (activity_name/unit/factor are all
    editable) — NOT a substitute for verifying against an authoritative
    source (EPA, DEFRA, IPCC, or your local regulator) before using
    figures derived from this table in an actual regulatory filing.
    """

    activity_name = models.CharField(max_length=255, help_text="e.g. 'Diesel combustion', 'Grid electricity'.")
    unit = models.CharField(max_length=50, help_text="e.g. 'liter', 'kWh', 'km'.")
    kg_co2e_per_unit = models.DecimalField(max_digits=12, decimal_places=6)
    source = models.CharField(max_length=255, blank=True, help_text="Reference for this factor.")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cycom_esg_emission_factors"
        ordering = ["activity_name"]

    def __str__(self):
        return f"{self.activity_name} ({self.kg_co2e_per_unit} kgCO2e/{self.unit})"


class EmissionEntry(BaseModel):
    """
    One logged activity — manual or CSV-imported entry, not auto-sourced
    from any other module yet (no Fleet/utility-metering module exists
    to pull real data from today). GHG Protocol scope categorization
    (Scope 1 direct, Scope 2 purchased energy, Scope 3 value chain) is
    the widely-used general framework, not a jurisdiction-specific one —
    map to your actual regulatory framework's categories separately if
    one applies to you.
    """

    SCOPE_CHOICES = [
        ("scope_1", "Scope 1 — Direct"),
        ("scope_2", "Scope 2 — Purchased Energy"),
        ("scope_3", "Scope 3 — Value Chain"),
    ]

    factor = models.ForeignKey(EmissionFactor, on_delete=models.PROTECT, related_name="entries")
    scope = models.CharField(max_length=10, choices=SCOPE_CHOICES)
    quantity = models.DecimalField(max_digits=14, decimal_places=4)
    activity_date = models.DateField()
    department = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    co2e_kg = models.DecimalField(max_digits=16, decimal_places=4, editable=False, default=Decimal("0"))

    class Meta:
        db_table = "cycom_esg_emission_entries"
        ordering = ["-activity_date"]

    def save(self, *args, **kwargs):
        self.co2e_kg = (self.quantity * self.factor.kg_co2e_per_unit).quantize(Decimal("0.0001"))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.factor.activity_name} x{self.quantity} = {self.co2e_kg} kgCO2e"
