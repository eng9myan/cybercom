from django.db import models

from platform.common.models import BaseModel
from products.cymed.core.patients.models import Patient


class Pregnancy(BaseModel):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="pregnancies")
    estimated_delivery_date = models.DateField()
    gravidity = models.PositiveIntegerField()
    parity = models.PositiveIntegerField()
    status = models.CharField(max_length=50, default="active")  # active, completed

    class Meta:
        db_table = "cymed_hospital_maternity_pregnancies"


class PrenatalEncounter(BaseModel):
    pregnancy = models.ForeignKey(Pregnancy, on_delete=models.CASCADE)
    encounter_date = models.DateTimeField(auto_now_add=True)
    gestational_weeks = models.DecimalField(max_digits=4, decimal_places=1)
    fetal_heart_rate = models.PositiveIntegerField(null=True, blank=True)
    maternal_bp_sys = models.PositiveIntegerField()
    maternal_bp_dia = models.PositiveIntegerField()
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_hospital_maternity_prenatal_encounters"


class LaborEpisode(BaseModel):
    pregnancy = models.OneToOneField(Pregnancy, on_delete=models.CASCADE, related_name="labor")
    admitted_at = models.DateTimeField(auto_now_add=True)
    stage_of_labor = models.PositiveSmallIntegerField(default=1)  # 1, 2, 3, 4
    cervical_dilation_cm = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)
    contractions_frequency_mins = models.PositiveIntegerField(null=True, blank=True)
    fetal_monitoring_status = models.CharField(max_length=100, default="normal")

    class Meta:
        db_table = "cymed_hospital_maternity_labor"


class Delivery(BaseModel):
    labor_episode = models.ForeignKey(
        LaborEpisode, on_delete=models.CASCADE, related_name="deliveries"
    )
    delivery_time = models.DateTimeField()
    delivery_method = models.CharField(max_length=100)  # vaginal, cesarean, vacuum, forceps
    apgar_1m = models.PositiveIntegerField()
    apgar_5m = models.PositiveIntegerField()
    outcome = models.CharField(max_length=100, default="live_birth")

    class Meta:
        db_table = "cymed_hospital_maternity_deliveries"


class NewbornRecord(BaseModel):
    delivery = models.ForeignKey(Delivery, on_delete=models.CASCADE, related_name="newborns")
    baby_patient = models.OneToOneField(Patient, on_delete=models.SET_NULL, null=True, blank=True)
    gender = models.CharField(max_length=10)  # male, female, unknown
    weight_grams = models.PositiveIntegerField()
    height_cm = models.DecimalField(max_digits=4, decimal_places=1)
    head_circumference_cm = models.DecimalField(max_digits=4, decimal_places=1)

    class Meta:
        db_table = "cymed_hospital_maternity_newborns"


class PostpartumCare(BaseModel):
    pregnancy = models.ForeignKey(Pregnancy, on_delete=models.CASCADE)
    checked_at = models.DateTimeField(auto_now_add=True)
    checked_by = models.UUIDField()
    maternal_condition = models.CharField(max_length=255)
    baby_condition = models.CharField(max_length=255)

    class Meta:
        db_table = "cymed_hospital_maternity_postpartum"
