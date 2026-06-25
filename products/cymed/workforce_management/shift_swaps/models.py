from django.db import models
from platform.common.models import BaseModel


SWAP_STATUS_CHOICES = [
    ("pending_recipient", "Pending Recipient Acceptance"),
    ("pending_validation", "Pending Validation"),
    ("pending_approval", "Pending Supervisor Approval"),
    ("approved", "Approved"),
    ("rejected", "Rejected"),
    ("cancelled", "Cancelled"),
    ("committed", "Committed"),
]

SWAP_REJECTION_REASON_CHOICES = [
    ("fatigue_violation", "Fatigue Constraint Violation"),
    ("credential_mismatch", "Credential Mismatch"),
    ("duty_hour_violation", "Duty Hour Violation"),
    ("rest_period_violation", "Rest Period Violation"),
    ("supervisor_rejected", "Supervisor Rejected"),
    ("recipient_declined", "Recipient Declined"),
    ("other", "Other"),
]

CALL_SWAP_GRADE_CHOICES = [
    ("resident_to_resident", "Resident-to-Resident"),
    ("consultant_to_consultant", "Consultant-to-Consultant"),
    ("other", "Other"),
]


class ShiftSwapRequest(BaseModel):
    class Meta:
        app_label = "cymed_hwm_swaps"
        db_table = "cymed_hwm_swaps_request"

    # Roster slot IDs from scheduling app (no model FK — cross-app ID reference)
    requester_profile_id = models.UUIDField(db_index=True)
    recipient_profile_id = models.UUIDField(db_index=True, null=True, blank=True)
    requester_slot_id = models.UUIDField(db_index=True)
    recipient_slot_id = models.UUIDField(db_index=True, null=True, blank=True)

    status = models.CharField(max_length=30, choices=SWAP_STATUS_CHOICES, default="pending_recipient")
    rejection_reason = models.CharField(max_length=40, choices=SWAP_REJECTION_REASON_CHOICES, blank=True)
    rejection_detail = models.TextField(blank=True)

    proposed_at = models.DateTimeField(auto_now_add=True)
    recipient_responded_at = models.DateTimeField(null=True, blank=True)
    committed_at = models.DateTimeField(null=True, blank=True)

    # Set when committed to track policy cache updates
    policy_cache_updated = models.BooleanField(default=False)

    def __str__(self):
        return f"Swap {self.requester_profile_id} -> {self.recipient_profile_id} ({self.status})"


class ShiftSwapApproval(BaseModel):
    class Meta:
        app_label = "cymed_hwm_swaps"
        db_table = "cymed_hwm_swaps_approval"

    swap_request = models.ForeignKey(
        ShiftSwapRequest,
        on_delete=models.CASCADE,
        related_name="approvals",
    )
    approver_id = models.UUIDField(db_index=True)
    approver_role = models.CharField(max_length=100)
    decision = models.CharField(max_length=10, choices=[("approved", "Approved"), ("rejected", "Rejected")])
    reason = models.TextField(blank=True)
    decided_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Approval {self.decision} by {self.approver_id}"


class SwapValidationLog(BaseModel):
    class Meta:
        app_label = "cymed_hwm_swaps"
        db_table = "cymed_hwm_swaps_validation_log"

    swap_request = models.ForeignKey(
        ShiftSwapRequest,
        on_delete=models.CASCADE,
        related_name="validation_logs",
    )
    check_type = models.CharField(max_length=50)
    passed = models.BooleanField()
    detail = models.TextField(blank=True)
    checked_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Validation {self.check_type}: {'PASS' if self.passed else 'FAIL'}"
