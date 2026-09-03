from django.db import models

from platform.common.models import BaseModel


class Vehicle(BaseModel):
    """Fleet vehicle. Odometer only moves forward (guarded in the serializer)."""

    STATUS_CHOICES = [
        ("active", "Active"),
        ("in_maintenance", "In Maintenance"),
        ("retired", "Retired"),
    ]

    name = models.CharField(max_length=150, blank=True)
    license_plate = models.CharField(max_length=50)
    make = models.CharField(max_length=100, blank=True)
    model = models.CharField(max_length=100, blank=True)
    driver_name = models.CharField(max_length=150, blank=True)
    odometer_km = models.DecimalField(max_digits=12, decimal_places=1, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    insurance_expiry = models.DateField(null=True, blank=True)
    license_expiry = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "cycom_fleet_vehicles"
        unique_together = [("tenant_id", "license_plate")]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.license_plate} ({self.make} {self.model})".strip()


class MaintenanceLog(BaseModel):
    MAINTENANCE_TYPES = [
        ("preventative", "Preventative"),
        ("corrective", "Corrective"),
        ("inspection", "Inspection"),
    ]

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="maintenance_logs")
    maintenance_date = models.DateField()
    maintenance_type = models.CharField(max_length=20, choices=MAINTENANCE_TYPES, default="preventative")
    cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    service_provider = models.CharField(max_length=150, blank=True)
    odometer_km = models.DecimalField(max_digits=12, decimal_places=1, default=0)
    next_service_km = models.DecimalField(max_digits=12, decimal_places=1, null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cycom_fleet_maintenance_logs"
        ordering = ["-maintenance_date"]

    def __str__(self):
        return f"{self.vehicle.license_plate} {self.maintenance_type} @ {self.maintenance_date}"


class FuelLog(BaseModel):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="fuel_logs")
    log_date = models.DateField()
    liters = models.DecimalField(max_digits=10, decimal_places=2)
    price_per_liter = models.DecimalField(max_digits=8, decimal_places=3)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2)
    fuel_station = models.CharField(max_length=150, blank=True)
    odometer_km = models.DecimalField(max_digits=12, decimal_places=1, default=0)

    class Meta:
        db_table = "cycom_fleet_fuel_logs"
        ordering = ["-log_date"]

    def __str__(self):
        return f"{self.vehicle.license_plate} {self.liters}L @ {self.log_date}"
