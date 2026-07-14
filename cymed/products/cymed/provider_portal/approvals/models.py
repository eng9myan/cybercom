from django.db import models

from platform.common.models import BaseModel


class ApprovalRequest(BaseModel):
    APPROVAL_TYPE_CHOICES = [
        ("medication_approval", "Medication Approval"),
        ("controlled_substance", "Controlled Substance"),
        ("leave_request", "Leave Request"),
        ("schedule_change", "Schedule Change"),
        ("procedure_authorization", "Procedure Authorization"),
        ("referral", "Referral"),
        ("discharge_override", "Discharge Override"),
        ("administrative", "Administrative"),
        ("clinical_protocol_deviation", "Clinical Protocol Deviation"),
        ("research", "Research"),
    ]
    PRIORITY_CHOICES = [
        ("routine", "Routine"),
        ("urgent", "Urgent"),
        ("stat", "STAT"),
    ]
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("cancelled", "Cancelled"),
        ("expired", "Expired"),
    ]

    approval_type = models.CharField(max_length=30, choices=APPROVAL_TYPE_CHOICES)
    title = models.CharField(max_length=500)
    description = models.TextField()
    requested_by_provider_id = models.UUIDField(db_index=True)
    requested_by_name = models.CharField(max_length=255)
    approver_id = models.UUIDField(db_index=True)
    approver_name = models.CharField(max_length=255)
    patient_id = models.UUIDField(null=True, blank=True, db_index=True)
    reference_id = models.UUIDField(null=True, blank=True)
    reference_type = models.CharField(max_length=100, blank=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default="routine")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    due_by = models.DateTimeField(null=True, blank=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    approval_notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    escalated_at = models.DateTimeField(null=True, blank=True)
    escalated_to = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = "cymed_prov_approval_requests"
        indexes = [
            models.Index(fields=["tenant_id", "approver_id", "status"]),
            models.Index(fields=["tenant_id", "requested_by_provider_id", "status"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.approval_type}) - {self.status}"


class ApprovalWorkflow(BaseModel):
    workflow_name = models.CharField(max_length=255)
    approval_type = models.CharField(max_length=30)
    steps = models.JSONField(default=list)
    is_sequential = models.BooleanField(default=True)
    requires_all_approvers = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_by_provider_id = models.UUIDField()
    specialty = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "cymed_prov_approval_workflows"

    def __str__(self):
        return f"{self.workflow_name} ({self.approval_type})"


class ApprovalDecision(BaseModel):
    DECISION_CHOICES = [
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("requested_more_info", "Requested More Info"),
        ("delegated", "Delegated"),
    ]

    approval_request = models.ForeignKey(
        ApprovalRequest,
        on_delete=models.CASCADE,
        related_name="decisions",
    )
    decided_by_provider_id = models.UUIDField()
    decided_by_name = models.CharField(max_length=255)
    decision = models.CharField(max_length=25, choices=DECISION_CHOICES)
    decision_notes = models.TextField(blank=True)
    conditions = models.TextField(blank=True)
    delegated_to = models.UUIDField(null=True, blank=True)
    step_order = models.PositiveSmallIntegerField(default=1)

    class Meta:
        db_table = "cymed_prov_approval_decisions"

    def __str__(self):
        return f"Decision '{self.decision}' by {self.decided_by_name} on request {self.approval_request_id}"


class ApprovalAuditLog(BaseModel):
    ACTION_CHOICES = [
        ("created", "Created"),
        ("submitted", "Submitted"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("cancelled", "Cancelled"),
        ("escalated", "Escalated"),
        ("delegated", "Delegated"),
        ("expired", "Expired"),
        ("viewed", "Viewed"),
    ]

    approval_request = models.ForeignKey(
        ApprovalRequest,
        on_delete=models.CASCADE,
        related_name="audit_log",
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    performed_by_provider_id = models.UUIDField()
    performed_by_name = models.CharField(max_length=255)
    details = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        db_table = "cymed_prov_approval_audit"

    def __str__(self):
        return f"Audit: {self.action} on request {self.approval_request_id} by {self.performed_by_name}"
