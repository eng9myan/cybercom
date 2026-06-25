from django.db import models
from platform.common.models import BaseModel


FORECAST_STATUS_CHOICES = [
    ("pending", "Pending"),
    ("generated", "Generated"),
    ("applied", "Applied to Roster"),
    ("superseded", "Superseded"),
]

CENSUS_SOURCE_CHOICES = [
    ("er_visits", "Emergency Room Visits"),
    ("inpatient_admissions", "Inpatient Admissions"),
    ("outpatient_calendar", "Outpatient Calendar"),
    ("surgical_schedule", "Surgical Schedule"),
    ("historical_trend", "Historical Trend"),
]


class CensusDataPoint(BaseModel):
    class Meta:
        app_label = "cymed_hwm_forecasting"
        db_table = "cymed_hwm_forecast_census_point"

    facility_id = models.UUIDField(db_index=True)
    department_id = models.UUIDField(db_index=True)
    census_date = models.DateField(db_index=True)
    actual_census = models.PositiveSmallIntegerField(default=0)
    source = models.CharField(max_length=30, choices=CENSUS_SOURCE_CHOICES)

    def __str__(self):
        return f"Census {self.facility_id} {self.census_date}: {self.actual_census}"


class StaffingForecast(BaseModel):
    class Meta:
        app_label = "cymed_hwm_forecasting"
        db_table = "cymed_hwm_forecast_staffing"

    facility_id = models.UUIDField(db_index=True)
    department_id = models.UUIDField(db_index=True)
    forecast_date = models.DateField(db_index=True)
    # CyAI model reference
    model_version = models.CharField(max_length=50, blank=True)
    generated_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=FORECAST_STATUS_CHOICES, default="pending")

    predicted_census = models.PositiveSmallIntegerField(default=0)
    recommended_fte = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    recommended_nurse_fte = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    recommended_physician_fte = models.DecimalField(max_digits=6, decimal_places=2, default=0)

    # Whether CyAI flagged a surge (influenza, heatwave, etc.)
    surge_predicted = models.BooleanField(default=False)
    surge_reason = models.CharField(max_length=200, blank=True)

    # Input data contract metadata
    input_data_snapshot = models.JSONField(default=dict)

    def __str__(self):
        return f"Forecast {self.facility_id} {self.forecast_date} — {self.status}"


class ForecastAdjustment(BaseModel):
    class Meta:
        app_label = "cymed_hwm_forecasting"
        db_table = "cymed_hwm_forecast_adjustment"

    forecast = models.ForeignKey(
        StaffingForecast,
        on_delete=models.CASCADE,
        related_name="adjustments",
    )
    adjusted_by_id = models.UUIDField(db_index=True)
    original_fte = models.DecimalField(max_digits=6, decimal_places=2)
    adjusted_fte = models.DecimalField(max_digits=6, decimal_places=2)
    reason = models.TextField()

    def __str__(self):
        return f"Adjustment {self.original_fte} -> {self.adjusted_fte} on {self.forecast_id}"


class ForecastRosterMapping(BaseModel):
    class Meta:
        app_label = "cymed_hwm_forecasting"
        db_table = "cymed_hwm_forecast_roster_map"

    forecast = models.ForeignKey(
        StaffingForecast,
        on_delete=models.CASCADE,
        related_name="roster_mappings",
    )
    roster_cycle_id = models.UUIDField(db_index=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    applied_by_id = models.UUIDField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Forecast -> Roster {self.roster_cycle_id}"
