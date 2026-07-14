from django.db import models

from platform.common.models import BaseModel
from products.cymed.core.patients.models import Patient


class EmergencyVisit(BaseModel):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    arrival_time = models.DateTimeField(auto_now_add=True)
    arrival_method = models.CharField(max_length=100)  # ambulance, walk-in, police, flight
    presenting_complaint = models.TextField()
    status = models.CharField(
        max_length=50,
        choices=[
            ("triage", "Triage"),
            ("fast_track", "Fast Track"),
            ("resuscitation", "Resuscitation"),
            ("observation", "Observation"),
            ("admitted", "Admitted"),
            ("discharged", "Discharged"),
        ],
        default="triage",
    )

    class Meta:
        db_table = "cymed_hospital_emergency_visits"


class EmergencyTriage(BaseModel):
    visit = models.OneToOneField(EmergencyVisit, on_delete=models.CASCADE, related_name="triage")
    esi_level = models.PositiveSmallIntegerField()  # Emergency Severity Index (1 to 5)
    chief_complaint = models.TextField()
    triage_nurse_id = models.UUIDField()
    logged_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cymed_hospital_emergency_triages"


class EmergencyAcuity(BaseModel):
    visit = models.ForeignKey(EmergencyVisit, on_delete=models.CASCADE)
    news2_score = models.PositiveIntegerField()
    calculated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cymed_hospital_emergency_acuities"


class EmergencyDisposition(BaseModel):
    visit = models.OneToOneField(
        EmergencyVisit, on_delete=models.CASCADE, related_name="disposition"
    )
    disposition_type = models.CharField(max_length=100)  # discharged, admitted, transferred, AMA
    notes = models.TextField(blank=True)
    logged_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cymed_hospital_emergency_dispositions"


class EmergencyObservation(BaseModel):
    visit = models.ForeignKey(EmergencyVisit, on_delete=models.CASCADE)
    observed_at = models.DateTimeField(auto_now_add=True)
    systolic_bp = models.PositiveIntegerField()
    diastolic_bp = models.PositiveIntegerField()
    heart_rate = models.PositiveIntegerField()
    resp_rate = models.PositiveIntegerField()
    temp_c = models.DecimalField(max_digits=4, decimal_places=2)
    o2_sat = models.PositiveIntegerField()
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_hospital_emergency_observations"


class EmergencyTracking(BaseModel):
    visit = models.ForeignKey(EmergencyVisit, on_delete=models.CASCADE)
    location_label = models.CharField(max_length=100)  # Bed A1, Waiting Room, Triage Desk
    entered_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cymed_hospital_emergency_tracking"
