from django.db import models
from platform.common.models import BaseModel

class CapacityRule(BaseModel):
    rule_name = models.CharField(max_length=255)
    metric_source = models.CharField(max_length=100)  # census, ed_waiting, icu_occupancy
    threshold_value = models.PositiveIntegerField()
    action_plan_name = models.CharField(max_length=255)

    class Meta:
        db_table = "cymed_hospital_capacity_rules"

class CapacityThreshold(BaseModel):
    rule = models.ForeignKey(CapacityRule, on_delete=models.CASCADE)
    current_value = models.PositiveIntegerField()
    status_level = models.CharField(max_length=50, default="normal")  # normal, warning, critical
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cymed_hospital_capacity_mgmt_thresholds"

class SurgePlan(BaseModel):
    name = models.CharField(max_length=255)
    trigger_condition = models.CharField(max_length=255)
    allocated_beds_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=False)

    class Meta:
        db_table = "cymed_hospital_surge_plans"

class OverflowUnit(BaseModel):
    name = models.CharField(max_length=255)
    temporary_capacity = models.PositiveIntegerField()
    current_occupancy = models.PositiveIntegerField(default=0)
    is_open = models.BooleanField(default=False)

    class Meta:
        db_table = "cymed_hospital_overflow_units"
