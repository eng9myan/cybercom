from django.db import models

from platform.common.models import BaseModel
from products.cymed.core.patients.models import Patient


class SurgicalCase(BaseModel):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    surgeon_id = models.UUIDField()
    procedure_code = models.CharField(max_length=100)  # validated via Terminology
    scheduled_start = models.DateTimeField()
    scheduled_end = models.DateTimeField()
    status = models.CharField(
        max_length=50,
        choices=[
            ("scheduled", "Scheduled"),
            ("pre_op", "Pre-Op"),
            ("intra_op", "Intra-Op"),
            ("post_op", "Post-Op"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        default="scheduled",
    )

    class Meta:
        db_table = "cymed_hospital_surgical_cases"


class SurgicalSchedule(BaseModel):
    surgical_case = models.OneToOneField(
        SurgicalCase, on_delete=models.CASCADE, related_name="schedule"
    )
    operating_room_id = models.UUIDField()
    allocated_date = models.DateField()

    class Meta:
        db_table = "cymed_hospital_surgical_schedules"


class ProcedureBooking(BaseModel):
    surgical_case = models.ForeignKey(SurgicalCase, on_delete=models.CASCADE)
    priority = models.CharField(
        max_length=50,
        choices=[("elective", "Elective"), ("urgent", "Urgent"), ("emergency", "Emergency")],
        default="elective",
    )

    class Meta:
        db_table = "cymed_hospital_procedure_bookings"


class ProcedureConsent(BaseModel):
    surgical_case = models.OneToOneField(
        SurgicalCase, on_delete=models.CASCADE, related_name="consent"
    )
    patient_signature_blob = models.TextField()
    witness_name = models.CharField(max_length=255)
    signed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cymed_hospital_procedure_consents"


class ProcedureChecklist(BaseModel):
    surgical_case = models.OneToOneField(
        SurgicalCase, on_delete=models.CASCADE, related_name="checklist"
    )
    sign_in_ok = models.BooleanField(default=False)  # Before anesthesia induction
    time_out_ok = models.BooleanField(default=False)  # Before skin incision
    sign_out_ok = models.BooleanField(default=False)  # Before patient leaves OR
    logged_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cymed_hospital_procedure_checklists"


class SurgicalTeam(BaseModel):
    surgical_case = models.ForeignKey(
        SurgicalCase, on_delete=models.CASCADE, related_name="team_members"
    )
    member_id = models.UUIDField()
    role = models.CharField(
        max_length=100
    )  # lead_surgeon, assistant_surgeon, anesthesiologist, scrub_nurse, circulating_nurse

    class Meta:
        db_table = "cymed_hospital_surgical_teams"


class SurgicalEquipment(BaseModel):
    surgical_case = models.ForeignKey(
        SurgicalCase, on_delete=models.CASCADE, related_name="equipments"
    )
    asset_serial = models.CharField(max_length=100)  # mapped to ERP asset serial
    sterilized_status = models.BooleanField(default=True)
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cymed_hospital_surgical_equipments"
