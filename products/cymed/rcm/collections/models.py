import uuid
from django.db import models
from platform.common.models import BaseModel


class CollectionCase(BaseModel):
    AGING_BUCKET_CHOICES = [
        ("current", "Current"),
        ("30_days", "30 Days"),
        ("60_days", "60 Days"),
        ("90_days", "90 Days"),
        ("120_days", "120 Days"),
        ("over_120", "Over 120 Days"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("payment_plan", "Payment Plan"),
        ("legal", "Legal"),
        ("written_off", "Written Off"),
        ("resolved", "Resolved"),
        ("closed", "Closed"),
    ]

    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical"),
    ]

    patient_id = models.UUIDField(db_index=True)
    patient_account_id = models.UUIDField(db_index=True)
    case_number = models.CharField(max_length=50, unique=True)
    outstanding_balance = models.DecimalField(max_digits=14, decimal_places=2)
    original_balance = models.DecimalField(max_digits=14, decimal_places=2)
    aging_bucket = models.CharField(
        max_length=20, choices=AGING_BUCKET_CHOICES, default="current"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="active"
    )
    priority = models.CharField(
        max_length=10, choices=PRIORITY_CHOICES, default="medium"
    )
    assigned_to_user_id = models.UUIDField(null=True, blank=True)
    last_contact_date = models.DateField(null=True, blank=True)
    next_follow_up_date = models.DateField(null=True, blank=True)
    ai_collection_risk_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_rcm_coll_cases"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Case {self.case_number} | {self.status} | {self.outstanding_balance}"


class CollectionAction(BaseModel):
    ACTION_TYPE_CHOICES = [
        ("phone_call", "Phone Call"),
        ("sms", "SMS"),
        ("email", "Email"),
        ("letter", "Letter"),
        ("payment_arrangement", "Payment Arrangement"),
        ("legal_notice", "Legal Notice"),
        ("field_visit", "Field Visit"),
        ("payment_received", "Payment Received"),
        ("plan_created", "Plan Created"),
        ("write_off_recommended", "Write-Off Recommended"),
    ]

    collection_case = models.ForeignKey(
        CollectionCase, on_delete=models.CASCADE, related_name="actions"
    )
    action_type = models.CharField(max_length=30, choices=ACTION_TYPE_CHOICES)
    action_date = models.DateTimeField(auto_now_add=True)
    performed_by_user_id = models.UUIDField()
    notes = models.TextField(blank=True)
    amount_collected = models.DecimalField(
        max_digits=12, decimal_places=2, default=0
    )
    next_action_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "cymed_rcm_coll_actions"
        ordering = ["-action_date"]

    def __str__(self):
        return f"Action {self.id} | {self.action_type} | Case {self.collection_case_id}"


class PaymentPlan(BaseModel):
    FREQUENCY_CHOICES = [
        ("weekly", "Weekly"),
        ("biweekly", "Bi-Weekly"),
        ("monthly", "Monthly"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("completed", "Completed"),
        ("defaulted", "Defaulted"),
        ("cancelled", "Cancelled"),
    ]

    collection_case = models.ForeignKey(
        CollectionCase, on_delete=models.PROTECT, related_name="payment_plans"
    )
    total_amount = models.DecimalField(max_digits=14, decimal_places=2)
    installment_amount = models.DecimalField(max_digits=12, decimal_places=2)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    number_of_installments = models.PositiveSmallIntegerField()
    amount_paid = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    amount_remaining = models.DecimalField(max_digits=14, decimal_places=2)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="active"
    )
    approved_by_user_id = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = "cymed_rcm_coll_payment_plans"
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"PaymentPlan {self.id} | {self.frequency} | {self.status}"
        )


class CollectionOutcome(BaseModel):
    OUTCOME_TYPE_CHOICES = [
        ("paid_in_full", "Paid in Full"),
        ("partial_payment", "Partial Payment"),
        ("payment_plan_completed", "Payment Plan Completed"),
        ("written_off", "Written Off"),
        ("legal_settlement", "Legal Settlement"),
        ("uncollectable", "Uncollectable"),
    ]

    collection_case = models.ForeignKey(
        CollectionCase, on_delete=models.CASCADE, related_name="outcomes"
    )
    outcome_date = models.DateField()
    outcome_type = models.CharField(max_length=30, choices=OUTCOME_TYPE_CHOICES)
    amount_recovered = models.DecimalField(
        max_digits=14, decimal_places=2, default=0
    )
    amount_written_off = models.DecimalField(
        max_digits=14, decimal_places=2, default=0
    )
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_rcm_coll_outcomes"
        ordering = ["-outcome_date"]

    def __str__(self):
        return f"Outcome {self.id} | {self.outcome_type} | Case {self.collection_case_id}"
