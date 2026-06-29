from django.db import models

from platform.common.models import BaseModel
from products.cymed.hospital.adt.models import Admission


class NursingShift(BaseModel):
    name = models.CharField(max_length=100)  # Day shift, Night shift
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        db_table = "cymed_hospital_nursing_shifts"


class NursingAssignment(BaseModel):
    nurse_id = models.UUIDField()
    ward_id = models.UUIDField()
    shift = models.ForeignKey(NursingShift, on_delete=models.CASCADE)
    assigned_date = models.DateField()

    class Meta:
        db_table = "cymed_hospital_nursing_assignments"


class NursingAssessment(BaseModel):
    admission = models.ForeignKey(Admission, on_delete=models.CASCADE)
    assessed_by = models.UUIDField()
    assessed_at = models.DateTimeField(auto_now_add=True)
    nursing_summary = models.TextField()

    class Meta:
        db_table = "cymed_hospital_nursing_assessments"


class NursingCarePlan(BaseModel):
    admission = models.ForeignKey(Admission, on_delete=models.CASCADE)
    goals = models.TextField()
    activities = models.TextField()

    class Meta:
        db_table = "cymed_hospital_nursing_careplans"


class NursingTask(BaseModel):
    admission = models.ForeignKey(Admission, on_delete=models.CASCADE)
    task_name = models.CharField(max_length=255)
    scheduled_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=50,
        choices=[("pending", "Pending"), ("completed", "Completed"), ("skipped", "Skipped")],
        default="pending",
    )

    class Meta:
        db_table = "cymed_hospital_nursing_tasks"


class NursingHandover(BaseModel):
    admission = models.ForeignKey(Admission, on_delete=models.CASCADE)
    outgoing_nurse_id = models.UUIDField()
    incoming_nurse_id = models.UUIDField()
    handover_time = models.DateTimeField(auto_now_add=True)
    situation_background = models.TextField()  # SBAR format
    assessment_recommendation = models.TextField()

    class Meta:
        db_table = "cymed_hospital_nursing_handovers"
