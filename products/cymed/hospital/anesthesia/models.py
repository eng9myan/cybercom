from django.db import models
from platform.common.models import BaseModel
from products.cymed.hospital.operating_room.models import SurgicalCase

class AnesthesiaAssessment(BaseModel):
    surgical_case = models.OneToOneField(SurgicalCase, on_delete=models.CASCADE, related_name="anesthesia_assessment")
    assessed_by = models.UUIDField()
    asa_class = models.CharField(max_length=50)  # ASA I, II, III, IV, V, VI
    airway_mallampati = models.PositiveSmallIntegerField()  # 1 to 4
    notes = models.TextField()

    class Meta:
        db_table = "cymed_hospital_anesthesia_assessments"

class AnesthesiaPlan(BaseModel):
    surgical_case = models.OneToOneField(SurgicalCase, on_delete=models.CASCADE, related_name="anesthesia_plan")
    anesthetic_type = models.CharField(max_length=100)  # general, spinal, epidural, local
    plan_description = models.TextField()

    class Meta:
        db_table = "cymed_hospital_anesthesia_plans"

class AnesthesiaRecord(BaseModel):
    surgical_case = models.OneToOneField(SurgicalCase, on_delete=models.CASCADE, related_name="anesthesia_record")
    anesthesiologist_id = models.UUIDField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    agents_used = models.JSONField()  # e.g., Propofol, Sevoflurane, Fentanyl
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_hospital_anesthesia_records"

class RecoveryAssessment(BaseModel):
    surgical_case = models.ForeignKey(SurgicalCase, on_delete=models.CASCADE)
    logged_at = models.DateTimeField(auto_now_add=True)
    aldrete_score = models.PositiveIntegerField()  # Activity, Respiration, Circulation, Consciousness, O2 Sat (0 to 10)
    comments = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_hospital_anesthesia_recovery_assessments"
