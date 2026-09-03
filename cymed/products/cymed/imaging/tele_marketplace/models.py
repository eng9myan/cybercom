"""Teleradiology marketplace domain models — providers, contracts, jobs, bids, reports."""

from __future__ import annotations

import uuid
from decimal import Decimal

from django.db import models
from django.utils import timezone

from platform.common.models import BaseModel


class RadiologistProvider(BaseModel):
    class Tier(models.TextChoices):
        GENERAL = "general", "General"
        SUBSPECIALTY = "subspecialty", "Subspecialty"
        EXPERT = "expert", "Expert"
        PAEDIATRIC_EXPERT = "paediatric_expert", "Paediatric Expert"

    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    display_name = models.CharField(max_length=255)
    organization = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=2, blank=True)
    licenses = models.JSONField(default=list, blank=True)
    modalities = models.JSONField(default=list, blank=True)
    body_parts = models.JSONField(default=list, blank=True)
    subspecialty = models.JSONField(default=list, blank=True)
    languages = models.JSONField(default=list, blank=True)
    tier = models.CharField(max_length=32, choices=Tier.choices, default=Tier.GENERAL)
    hourly_rate = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    per_study_rate = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    currency = models.CharField(max_length=3, default="USD")
    sla_urgent_minutes = models.IntegerField(default=30)
    sla_routine_minutes = models.IntegerField(default=240)
    active = models.BooleanField(default=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal("0"))

    class Meta:
        app_label = "cymed_img_tele_marketplace"
        db_table = "cymed_img_tele_marketplace_radiologist_provider"

    def __str__(self) -> str:
        return f"{self.display_name} ({self.tier})"


class ReadContract(BaseModel):
    class PaymentTerms(models.TextChoices):
        PER_STUDY = "per_study", "Per Study"
        PER_HOUR = "per_hour", "Per Hour"
        RETAINER = "retainer", "Retainer"
        HYBRID = "hybrid", "Hybrid"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"
        TERMINATED = "terminated", "Terminated"

    provider = models.ForeignKey(
        RadiologistProvider,
        on_delete=models.CASCADE,
        related_name="contracts",
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    payment_terms = models.CharField(
        max_length=32,
        choices=PaymentTerms.choices,
        default=PaymentTerms.PER_STUDY,
    )
    payment_amount = models.DecimalField(
        max_digits=18, decimal_places=4, null=True, blank=True
    )
    currency = models.CharField(max_length=3, default="USD")
    modalities = models.JSONField(default=list, blank=True)
    nda_signed = models.BooleanField(default=False)
    liability_insurance_verified = models.BooleanField(default=False)
    status = models.CharField(
        max_length=32, choices=Status.choices, default=Status.DRAFT
    )

    class Meta:
        app_label = "cymed_img_tele_marketplace"
        db_table = "cymed_img_tele_marketplace_read_contract"

    def __str__(self) -> str:
        return f"Contract {self.id} — {self.status}"


class TeleReadJob(BaseModel):
    class Priority(models.TextChoices):
        STAT = "stat", "STAT"
        URGENT = "urgent", "Urgent"
        ROUTINE = "routine", "Routine"

    class Status(models.TextChoices):
        CREATED = "created", "Created"
        POSTED = "posted", "Posted"
        BIDS_OPEN = "bids_open", "Bids Open"
        ASSIGNED = "assigned", "Assigned"
        IN_PROGRESS = "in_progress", "In Progress"
        DRAFT_REPORT = "draft_report", "Draft Report"
        FINAL_REPORT = "final_report", "Final Report"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"
        DISPUTED = "disputed", "Disputed"

    study_instance_uid = models.CharField(max_length=128, db_index=True)
    ordered_by_profile_id = models.UUIDField(null=True, blank=True)
    patient_profile_id = models.UUIDField(null=True, blank=True)
    modality = models.CharField(max_length=32)
    body_part = models.CharField(max_length=64, blank=True)
    priority = models.CharField(
        max_length=32, choices=Priority.choices, default=Priority.ROUTINE
    )
    assigned_provider = models.ForeignKey(
        RadiologistProvider,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_jobs",
    )
    contract = models.ForeignKey(
        ReadContract,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="jobs",
    )
    status = models.CharField(
        max_length=32, choices=Status.choices, default=Status.CREATED
    )
    requested_at = models.DateTimeField(default=timezone.now)
    assigned_at = models.DateTimeField(null=True, blank=True)
    draft_at = models.DateTimeField(null=True, blank=True)
    final_at = models.DateTimeField(null=True, blank=True)
    sla_deadline_at = models.DateTimeField(null=True, blank=True)
    payout_amount = models.DecimalField(
        max_digits=18, decimal_places=4, default=Decimal("0")
    )
    currency = models.CharField(max_length=3, default="USD")

    class Meta:
        app_label = "cymed_img_tele_marketplace"
        db_table = "cymed_img_tele_marketplace_tele_read_job"

    def __str__(self) -> str:
        return f"Job {self.id} — {self.study_instance_uid} [{self.status}]"


class Bid(BaseModel):
    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"
        WITHDRAWN = "withdrawn", "Withdrawn"
        EXPIRED = "expired", "Expired"

    job = models.ForeignKey(
        TeleReadJob, on_delete=models.CASCADE, related_name="bids"
    )
    provider = models.ForeignKey(
        RadiologistProvider, on_delete=models.CASCADE, related_name="bids"
    )
    amount = models.DecimalField(max_digits=18, decimal_places=4)
    currency = models.CharField(max_length=3, default="USD")
    eta_minutes = models.IntegerField()
    status = models.CharField(
        max_length=32, choices=Status.choices, default=Status.SUBMITTED
    )
    submitted_at = models.DateTimeField(default=timezone.now)
    note = models.TextField(blank=True)

    class Meta:
        app_label = "cymed_img_tele_marketplace"
        db_table = "cymed_img_tele_marketplace_bid"

    def __str__(self) -> str:
        return f"Bid {self.id} — job {self.job_id} [{self.status}]"


class TeleReport(BaseModel):
    class Kind(models.TextChoices):
        PRELIMINARY = "preliminary", "Preliminary"
        FINAL = "final", "Final"
        ADDENDUM = "addendum", "Addendum"

    job = models.ForeignKey(
        TeleReadJob, on_delete=models.CASCADE, related_name="reports"
    )
    version = models.IntegerField(default=1)
    kind = models.CharField(
        max_length=32, choices=Kind.choices, default=Kind.PRELIMINARY
    )
    text = models.TextField(blank=True)
    findings = models.JSONField(default=dict, blank=True)
    impressions = models.TextField(blank=True)
    submitted_by_provider = models.ForeignKey(
        RadiologistProvider,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    submitted_at = models.DateTimeField(default=timezone.now)
    signed = models.BooleanField(default=False)

    class Meta:
        app_label = "cymed_img_tele_marketplace"
        db_table = "cymed_img_tele_marketplace_tele_report"

    def __str__(self) -> str:
        return f"Report {self.id} v{self.version} — {self.kind}"
