from django.db import models

from platform.common.models import BaseModel
from products.cymed.hospital.inpatient.models import HospitalStay


class ICUStay(BaseModel):
    stay = models.OneToOneField(HospitalStay, on_delete=models.CASCADE, related_name="icu_details")
    icu_admitted_at = models.DateTimeField(auto_now_add=True)
    icu_released_at = models.DateTimeField(null=True, blank=True)
    ventilator_status = models.CharField(
        max_length=50, default="none"
    )  # none, non_invasive, invasive
    invasive_lines_count = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "cymed_hospital_icu_stays"


class ICURound(BaseModel):
    icu_stay = models.ForeignKey(ICUStay, on_delete=models.CASCADE, related_name="rounds")
    recorded_at = models.DateTimeField(auto_now_add=True)
    recorded_by = models.UUIDField()
    heart_rate = models.PositiveIntegerField()
    mean_arterial_pressure = models.PositiveIntegerField()
    temp_c = models.DecimalField(max_digits=4, decimal_places=2)
    resp_rate = models.PositiveIntegerField()
    o2_sat = models.PositiveIntegerField()

    class Meta:
        db_table = "cymed_hospital_icu_rounds"


class ICUAssessment(BaseModel):
    icu_stay = models.ForeignKey(ICUStay, on_delete=models.CASCADE)
    assessed_at = models.DateTimeField(auto_now_add=True)
    sofa_score = models.PositiveIntegerField()
    apache_ii_score = models.PositiveIntegerField()
    glasgow_coma_scale = models.PositiveIntegerField()

    class Meta:
        db_table = "cymed_hospital_icu_assessments"


class VentilatorRecord(BaseModel):
    icu_stay = models.ForeignKey(ICUStay, on_delete=models.CASCADE)
    logged_at = models.DateTimeField(auto_now_add=True)
    logged_by = models.UUIDField()
    mode = models.CharField(max_length=100)  # AC, SIMV, PSV, CPAP
    fio2_pct = models.PositiveIntegerField()  # Oxygen fraction (e.g. 40 means 40%)
    peep = models.PositiveIntegerField()  # Positive end-expiratory pressure
    rate = models.PositiveIntegerField()  # Respiratory rate on vent

    class Meta:
        db_table = "cymed_hospital_icu_ventilators"


class CriticalEvent(BaseModel):
    icu_stay = models.ForeignKey(ICUStay, on_delete=models.CASCADE)
    event_time = models.DateTimeField(auto_now_add=True)
    event_type = models.CharField(max_length=100)  # cardiac_arrest, intubation, line_displacement
    details = models.TextField()
    actions_taken = models.TextField()

    class Meta:
        db_table = "cymed_hospital_icu_critical_events"
