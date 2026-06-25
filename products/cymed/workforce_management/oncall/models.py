from django.db import models
from platform.common.models import BaseModel


CALL_MODE_CHOICES = [
    ("in_house", "In-House (< 5 min response)"),
    ("home_call", "Home Call (< 30 min response)"),
    ("emergency", "Emergency Call"),
]

CALL_TIER_CHOICES = [
    ("primary", "Primary (First Responder)"),
    ("secondary", "Secondary (Backup)"),
    ("backup", "Backup (Tertiary)"),
]

CALL_SENIORITY_CHOICES = [
    ("resident", "Resident Call"),
    ("consultant", "Consultant Call"),
    ("emergency", "Emergency Activation"),
]

ONCALL_ROSTER_STATUS_CHOICES = [
    ("draft", "Draft"),
    ("validated", "Validated"),
    ("published", "Published"),
    ("active", "Active"),
    ("closed", "Closed"),
]

PAGE_STATUS_CHOICES = [
    ("sent", "Sent"),
    ("acknowledged", "Acknowledged"),
    ("escalated", "Escalated"),
    ("resolved", "Resolved"),
    ("missed", "Missed"),
]

URGENCY_CHOICES = [
    ("routine", "Routine"),
    ("urgent", "Urgent"),
    ("emergent", "Emergent"),
    ("critical", "Critical"),
]


class OnCallRoster(BaseModel):
    class Meta:
        app_label = "cymed_hwm_oncall"
        db_table = "cymed_hwm_oncall_roster"

    facility_id = models.UUIDField(db_index=True)
    department_id = models.UUIDField(db_index=True)
    specialty = models.CharField(max_length=100)
    roster_date = models.DateField(db_index=True)
    status = models.CharField(max_length=20, choices=ONCALL_ROSTER_STATUS_CHOICES, default="draft")
    published_by_id = models.UUIDField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"On-Call Roster {self.specialty} — {self.roster_date} ({self.status})"


class OnCallAssignment(BaseModel):
    class Meta:
        app_label = "cymed_hwm_oncall"
        db_table = "cymed_hwm_oncall_assignment"
        unique_together = [["tenant_id", "oncall_roster", "call_tier"]]

    oncall_roster = models.ForeignKey(
        OnCallRoster,
        on_delete=models.CASCADE,
        related_name="assignments",
    )
    workforce_profile_id = models.UUIDField(db_index=True)
    call_mode = models.CharField(max_length=20, choices=CALL_MODE_CHOICES)
    call_tier = models.CharField(max_length=20, choices=CALL_TIER_CHOICES)
    call_seniority = models.CharField(max_length=20, choices=CALL_SENIORITY_CHOICES)
    # Response SLA in minutes
    response_sla_minutes = models.PositiveSmallIntegerField(default=30)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.call_tier} ({self.call_mode}) — {self.workforce_profile_id}"


class OnCallPage(BaseModel):
    class Meta:
        app_label = "cymed_hwm_oncall"
        db_table = "cymed_hwm_oncall_page"

    oncall_roster = models.ForeignKey(
        OnCallRoster,
        on_delete=models.PROTECT,
        related_name="pages",
    )
    initiating_ward_id = models.UUIDField(db_index=True)
    patient_id = models.UUIDField(null=True, blank=True)
    urgency = models.CharField(max_length=20, choices=URGENCY_CHOICES, default="urgent")
    clinical_reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=PAGE_STATUS_CHOICES, default="sent")
    triggered_at = models.DateTimeField(auto_now_add=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by_id = models.UUIDField(null=True, blank=True)
    # SLA timer — populated when the page is sent
    sla_deadline = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Page {self.urgency} — {self.status} ({self.triggered_at})"


class OnCallEscalation(BaseModel):
    class Meta:
        app_label = "cymed_hwm_oncall"
        db_table = "cymed_hwm_oncall_escalation"

    page = models.ForeignKey(
        OnCallPage,
        on_delete=models.CASCADE,
        related_name="escalations",
    )
    escalation_level = models.PositiveSmallIntegerField()
    escalated_to_profile_id = models.UUIDField(db_index=True)
    triggered_at = models.DateTimeField(auto_now_add=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    sla_deadline = models.DateTimeField(null=True, blank=True)
    department_chair_alerted = models.BooleanField(default=False)

    def __str__(self):
        return f"Escalation L{self.escalation_level} — page {self.page_id}"


class CallSwapRequest(BaseModel):
    class Meta:
        app_label = "cymed_hwm_oncall"
        db_table = "cymed_hwm_oncall_call_swap"

    original_assignment = models.ForeignKey(
        OnCallAssignment,
        on_delete=models.PROTECT,
        related_name="swap_requests",
    )
    requester_profile_id = models.UUIDField(db_index=True)
    recipient_profile_id = models.UUIDField(db_index=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        default="pending",
    )
    approver_id = models.UUIDField(null=True, blank=True)
    approver_role = models.CharField(max_length=100, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    # After approval, update Redis policy cache for correct page routing
    policy_cache_updated = models.BooleanField(default=False)

    def __str__(self):
        return f"Call Swap {self.requester_profile_id} -> {self.recipient_profile_id} ({self.status})"
