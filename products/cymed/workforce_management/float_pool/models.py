from django.db import models
from platform.common.models import BaseModel


FLOAT_ASSIGNMENT_STATUS_CHOICES = [
    ("available", "Available"),
    ("deployed", "Deployed"),
    ("recalled", "Recalled"),
    ("unavailable", "Unavailable"),
]

AGENCY_STAFF_STATUS_CHOICES = [
    ("pending_verification", "Pending Verification"),
    ("active", "Active"),
    ("expired", "Expired"),
    ("terminated", "Terminated"),
]

SHORTAGE_ESCALATION_LEVEL_CHOICES = [
    ("level_0", "Level 0 — Float Pool Available"),
    ("level_1", "Level 1 — Head Nurse Notified"),
    ("level_2", "Level 2 — Nurse Manager Notified"),
    ("level_3", "Level 3 — Diversion / Admission Caps"),
]


class FloatPoolMember(BaseModel):
    class Meta:
        app_label = "cymed_hwm_float_pool"
        db_table = "cymed_hwm_float_pool_member"
        unique_together = [["tenant_id", "workforce_profile_id"]]

    workforce_profile_id = models.UUIDField(db_index=True)
    facility_id = models.UUIDField(db_index=True)
    # Departments this float member is certified for
    eligible_department_ids = models.JSONField(default=list)
    eligible_ward_types = models.JSONField(default=list)
    priority_score = models.PositiveSmallIntegerField(default=50)
    is_network_float = models.BooleanField(default=False)

    def __str__(self):
        return f"Float Member {self.workforce_profile_id}"


class FloatDeployment(BaseModel):
    class Meta:
        app_label = "cymed_hwm_float_pool"
        db_table = "cymed_hwm_float_pool_deployment"

    float_member = models.ForeignKey(
        FloatPoolMember,
        on_delete=models.PROTECT,
        related_name="deployments",
    )
    target_department_id = models.UUIDField(db_index=True)
    target_facility_id = models.UUIDField(db_index=True)
    roster_slot_id = models.UUIDField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=FLOAT_ASSIGNMENT_STATUS_CHOICES, default="deployed")
    deployed_at = models.DateTimeField(auto_now_add=True)
    recalled_at = models.DateTimeField(null=True, blank=True)
    deployment_reason = models.TextField(blank=True)

    def __str__(self):
        return f"Float Deployment to {self.target_department_id} ({self.status})"


class AgencyStaffRegistration(BaseModel):
    class Meta:
        app_label = "cymed_hwm_float_pool"
        db_table = "cymed_hwm_float_pool_agency_staff"

    facility_id = models.UUIDField(db_index=True)
    agency_name = models.CharField(max_length=200)
    display_name = models.CharField(max_length=200)
    specialty = models.CharField(max_length=100)
    role_type = models.CharField(max_length=40)

    contract_start = models.DateField()
    contract_end = models.DateField()

    credential_verified = models.BooleanField(default=False)
    credential_verified_at = models.DateTimeField(null=True, blank=True)
    # CyIdentity digital check-in token
    identity_verified = models.BooleanField(default=False)
    identity_verified_at = models.DateTimeField(null=True, blank=True)

    # Issued after both verifications pass
    ehr_access_token_issued = models.BooleanField(default=False)
    status = models.CharField(max_length=30, choices=AGENCY_STAFF_STATUS_CHOICES, default="pending_verification")

    def __str__(self):
        return f"{self.display_name} ({self.agency_name}) — {self.status}"


class StaffingShortageAlert(BaseModel):
    class Meta:
        app_label = "cymed_hwm_float_pool"
        db_table = "cymed_hwm_float_pool_shortage_alert"

    facility_id = models.UUIDField(db_index=True)
    department_id = models.UUIDField(db_index=True)
    roster_slot_id = models.UUIDField(db_index=True)
    escalation_level = models.CharField(max_length=20, choices=SHORTAGE_ESCALATION_LEVEL_CHOICES)
    triggered_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_method = models.CharField(max_length=100, blank=True)
    diversion_activated = models.BooleanField(default=False)

    def __str__(self):
        return f"Shortage Alert {self.escalation_level} — dept {self.department_id}"
