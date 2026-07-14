from django.db import models

from platform.common.models import BaseModel


class PayerPortalAccount(BaseModel):
    ACCOUNT_ROLE_CHOICES = [
        ("claims_reviewer", "Claims Reviewer"),
        ("eligibility_reviewer", "Eligibility Reviewer"),
        ("auth_reviewer", "Authorization Reviewer"),
        ("appeals_reviewer", "Appeals Reviewer"),
        ("account_manager", "Account Manager"),
        ("admin", "Admin"),
    ]
    ACCESS_LEVEL_CHOICES = [
        ("read_only", "Read Only"),
        ("reviewer", "Reviewer"),
        ("approver", "Approver"),
        ("admin", "Admin"),
    ]

    insurance_company_id = models.UUIDField(db_index=True)
    cyidentity_user_id = models.UUIDField(db_index=True)
    account_role = models.CharField(max_length=30, choices=ACCOUNT_ROLE_CHOICES)
    is_active = models.BooleanField(default=True)
    access_level = models.CharField(max_length=20, choices=ACCESS_LEVEL_CHOICES, default="reviewer")
    last_login = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = "cymed_rcm_payer_portal"
        db_table = "cymed_rcm_payer_accounts"
        ordering = ["-created_at"]
        unique_together = [["tenant_id", "insurance_company_id", "cyidentity_user_id"]]
        indexes = [
            models.Index(fields=["tenant_id", "insurance_company_id"]),
            models.Index(fields=["tenant_id", "cyidentity_user_id"]),
        ]

    def __str__(self):
        return f"PayerPortalAccount({self.insurance_company_id} | {self.account_role})"


class PayerDashboard(BaseModel):
    payer_account = models.OneToOneField(
        PayerPortalAccount, on_delete=models.CASCADE, related_name="dashboard"
    )
    pending_claims_count = models.PositiveIntegerField(default=0)
    pending_auths_count = models.PositiveIntegerField(default=0)
    pending_appeals_count = models.PositiveIntegerField(default=0)
    last_refreshed_at = models.DateTimeField(null=True, blank=True)
    dashboard_config = models.JSONField(default=dict)

    class Meta:
        app_label = "cymed_rcm_payer_portal"
        db_table = "cymed_rcm_payer_dashboards"

    def __str__(self):
        return f"PayerDashboard({self.payer_account_id})"


class PayerClaimReview(BaseModel):
    REVIEW_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("under_review", "Under Review"),
        ("additional_info_requested", "Additional Info Requested"),
        ("decision_made", "Decision Made"),
    ]
    DECISION_CHOICES = [
        ("approved", "Approved"),
        ("denied", "Denied"),
        ("partial", "Partial"),
        ("pending", "Pending"),
    ]

    payer_account = models.ForeignKey(
        PayerPortalAccount, on_delete=models.PROTECT, related_name="claim_reviews"
    )
    claim_id = models.UUIDField(db_index=True)
    review_status = models.CharField(
        max_length=30, choices=REVIEW_STATUS_CHOICES, default="pending"
    )
    reviewer_notes = models.TextField(blank=True)
    decision = models.CharField(max_length=20, blank=True, choices=DECISION_CHOICES)
    decision_date = models.DateTimeField(null=True, blank=True)
    additional_info_requested = models.TextField(blank=True)
    info_due_date = models.DateField(null=True, blank=True)

    class Meta:
        app_label = "cymed_rcm_payer_portal"
        db_table = "cymed_rcm_payer_claim_reviews"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant_id", "payer_account_id", "review_status"]),
            models.Index(fields=["tenant_id", "claim_id"]),
        ]

    def __str__(self):
        return f"PayerClaimReview({self.claim_id} | {self.review_status})"


class PayerAuthorizationReview(BaseModel):
    REVIEW_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("under_review", "Under Review"),
        ("clinical_review", "Clinical Review"),
        ("decision_made", "Decision Made"),
    ]
    DECISION_CHOICES = [
        ("approved", "Approved"),
        ("partially_approved", "Partially Approved"),
        ("denied", "Denied"),
        ("pending_info", "Pending Info"),
    ]

    payer_account = models.ForeignKey(
        PayerPortalAccount, on_delete=models.PROTECT, related_name="auth_reviews"
    )
    preauthorization_id = models.UUIDField(db_index=True)
    review_status = models.CharField(
        max_length=30, choices=REVIEW_STATUS_CHOICES, default="pending"
    )
    reviewer_notes = models.TextField(blank=True)
    decision = models.CharField(max_length=20, blank=True, choices=DECISION_CHOICES)
    approved_units = models.PositiveIntegerField(null=True, blank=True)
    approved_start_date = models.DateField(null=True, blank=True)
    approved_end_date = models.DateField(null=True, blank=True)
    decision_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = "cymed_rcm_payer_portal"
        db_table = "cymed_rcm_payer_auth_reviews"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant_id", "payer_account_id", "review_status"]),
            models.Index(fields=["tenant_id", "preauthorization_id"]),
        ]

    def __str__(self):
        return f"PayerAuthorizationReview({self.preauthorization_id} | {self.review_status})"
