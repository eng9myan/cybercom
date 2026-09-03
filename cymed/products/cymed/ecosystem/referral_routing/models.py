"""Models for the CyMed Ecosystem cross-provider referral routing engine."""
from __future__ import annotations

import uuid
from decimal import Decimal

from django.db import models
from django.utils import timezone

from platform.common.models import BaseModel


class RoutingRule(BaseModel):
    class SourceKind(models.TextChoices):
        CLINIC = "clinic", "Clinic"
        HOSPITAL = "hospital", "Hospital"
        PHARMACY = "pharmacy", "Pharmacy"
        LAB = "lab", "Lab"
        IMAGING = "imaging", "Imaging"
        TELEHEALTH = "telehealth", "Telehealth"
        ANY = "any", "Any"

    class TargetKind(models.TextChoices):
        CLINIC = "clinic", "Clinic"
        HOSPITAL = "hospital", "Hospital"
        PHARMACY = "pharmacy", "Pharmacy"
        LAB = "lab", "Lab"
        IMAGING = "imaging", "Imaging"
        TELEHEALTH = "telehealth", "Telehealth"

    class Urgency(models.TextChoices):
        ROUTINE = "routine", "Routine"
        URGENT = "urgent", "Urgent"
        STAT = "stat", "STAT"

    class GeoScope(models.TextChoices):
        SAME_CITY = "same_city", "Same City"
        SAME_COUNTRY = "same_country", "Same Country"
        CROSS_BORDER = "cross_border", "Cross Border"
        ANYWHERE = "anywhere", "Anywhere"

    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=255)
    source_kind = models.CharField(max_length=32, choices=SourceKind.choices)
    target_kind = models.CharField(max_length=32, choices=TargetKind.choices)
    specialty = models.CharField(max_length=64, blank=True)
    urgency = models.CharField(max_length=32, choices=Urgency.choices, default=Urgency.ROUTINE)
    geo_scope = models.CharField(max_length=32, choices=GeoScope.choices, default=GeoScope.SAME_COUNTRY)
    preferred_tenant_ids = models.JSONField(default=list)
    fallback_tenant_ids = models.JSONField(default=list)
    payer_ids = models.JSONField(default=list)
    priority = models.IntegerField(default=100)
    active = models.BooleanField(default=True)

    class Meta:
        db_table = "cymed_eco_referral_routing_routing_rule"
        unique_together = [("tenant_id", "code")]

    def __str__(self) -> str:
        return f"RoutingRule({self.code}:{self.name})"


class NetworkReferral(BaseModel):
    class TargetKind(models.TextChoices):
        CLINIC = "clinic", "Clinic"
        HOSPITAL = "hospital", "Hospital"
        PHARMACY = "pharmacy", "Pharmacy"
        LAB = "lab", "Lab"
        IMAGING = "imaging", "Imaging"
        TELEHEALTH = "telehealth", "Telehealth"

    class Urgency(models.TextChoices):
        ROUTINE = "routine", "Routine"
        URGENT = "urgent", "Urgent"
        STAT = "stat", "STAT"

    class Status(models.TextChoices):
        CREATED = "created", "Created"
        ROUTED = "routed", "Routed"
        ACKNOWLEDGED = "acknowledged", "Acknowledged"
        SCHEDULED = "scheduled", "Scheduled"
        COMPLETED = "completed", "Completed"
        RESULT_RETURNED = "result_returned", "Result Returned"
        DECLINED = "declined", "Declined"
        EXPIRED = "expired", "Expired"
        WITHDRAWN = "withdrawn", "Withdrawn"

    source_tenant_id = models.UUIDField(db_index=True)
    source_provider_id = models.UUIDField(null=True, blank=True)
    target_tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    target_provider_id = models.UUIDField(null=True, blank=True)
    target_kind = models.CharField(max_length=32, choices=TargetKind.choices)
    patient_profile_id = models.UUIDField(db_index=True)
    reason = models.CharField(max_length=255)
    clinical_summary = models.TextField(blank=True)
    urgency = models.CharField(max_length=32, choices=Urgency.choices, default=Urgency.ROUTINE)
    preferred_locations = models.JSONField(default=list)
    consent_grant_id = models.UUIDField(null=True, blank=True)
    matched_rule_id = models.UUIDField(null=True, blank=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.CREATED)
    routed_at = models.DateTimeField(null=True, blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    result_documents = models.JSONField(default=list)

    class Meta:
        db_table = "cymed_eco_referral_routing_network_referral"

    def __str__(self) -> str:
        return f"NetworkReferral({self.id}:{self.status})"


class RoutingLog(BaseModel):
    class Kind(models.TextChoices):
        RULE_MATCHED = "rule_matched", "Rule Matched"
        CANDIDATE_SELECTED = "candidate_selected", "Candidate Selected"
        CANDIDATE_DECLINED = "candidate_declined", "Candidate Declined"
        FALLBACK_USED = "fallback_used", "Fallback Used"
        MANUAL_OVERRIDE = "manual_override", "Manual Override"
        EXPIRED = "expired", "Expired"

    referral = models.ForeignKey(
        NetworkReferral,
        on_delete=models.CASCADE,
        related_name="logs",
    )
    at = models.DateTimeField(default=timezone.now)
    kind = models.CharField(max_length=32, choices=Kind.choices)
    candidate_tenant_id = models.UUIDField(null=True, blank=True)
    rule_id = models.UUIDField(null=True, blank=True)
    reason = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_eco_referral_routing_routing_log"

    def __str__(self) -> str:
        return f"RoutingLog({self.referral_id}:{self.kind})"
