"""Data models for the CyMed provider network directory."""
from __future__ import annotations

import uuid
from decimal import Decimal

from django.db import models
from django.utils import timezone

from platform.common.models import BaseModel


class NetworkFacility(BaseModel):
    class Kind(models.TextChoices):
        CLINIC = "clinic", "Clinic"
        HOSPITAL = "hospital", "Hospital"
        PHARMACY = "pharmacy", "Pharmacy"
        LAB = "lab", "Lab"
        IMAGING_CENTER = "imaging_center", "Imaging Center"
        TELEHEALTH_DESK = "telehealth_desk", "Telehealth Desk"
        DENTAL = "dental", "Dental"

    tenant_id = models.UUIDField(db_index=True)
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=255)
    name_ar = models.CharField(max_length=255, blank=True)
    kind = models.CharField(max_length=32, choices=Kind.choices, default=Kind.CLINIC)
    country = models.CharField(max_length=2, blank=True)
    city = models.CharField(max_length=64, blank=True)
    address = models.JSONField(default=dict)
    lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    email = models.CharField(max_length=255, blank=True)
    website = models.URLField(blank=True)
    specialties = models.JSONField(default=list)
    services = models.JSONField(default=list)
    languages = models.JSONField(default=list)
    accepts_insurers = models.JSONField(default=list)
    accreditations = models.JSONField(default=list)
    hours = models.JSONField(default=dict)
    telehealth_capable = models.BooleanField(default=False)
    home_visit_capable = models.BooleanField(default=False)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal("0"))
    review_count = models.IntegerField(default=0)
    active = models.BooleanField(default=True)

    class Meta:
        db_table = "cymed_eco_provider_directory_network_facility"
        unique_together = [("tenant_id", "code")]

    def __str__(self) -> str:
        return f"{self.code} — {self.name}"


class NetworkPractitioner(BaseModel):
    tenant_id = models.UUIDField(db_index=True)
    user_profile_id = models.UUIDField(null=True, blank=True)
    first_name = models.CharField(max_length=128)
    last_name = models.CharField(max_length=128)
    display_name = models.CharField(max_length=255, blank=True)
    gender = models.CharField(max_length=16, blank=True)
    specialty = models.CharField(max_length=64, blank=True)
    subspecialties = models.JSONField(default=list)
    primary_facility = models.ForeignKey(
        NetworkFacility,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="primary_practitioners",
    )
    languages = models.JSONField(default=list)
    years_experience = models.IntegerField(default=0)
    consultation_fee = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    currency = models.CharField(max_length=3, default="SAR")
    teleconsultation_capable = models.BooleanField(default=False)
    accepts_new_patients = models.BooleanField(default=True)
    photo_url = models.URLField(blank=True)
    bio = models.TextField(blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal("0"))
    review_count = models.IntegerField(default=0)
    active = models.BooleanField(default=True)

    class Meta:
        db_table = "cymed_eco_provider_directory_network_practitioner"

    def __str__(self) -> str:
        return self.display_name or f"{self.first_name} {self.last_name}".strip()


class PractitionerFacilityAffiliation(BaseModel):
    class Role(models.TextChoices):
        ATTENDING = "attending", "Attending"
        CONSULTANT = "consultant", "Consultant"
        VISITING = "visiting", "Visiting"
        ON_CALL = "on_call", "On Call"
        OWNER = "owner", "Owner"

    practitioner = models.ForeignKey(
        NetworkPractitioner,
        on_delete=models.CASCADE,
        related_name="affiliations",
    )
    facility = models.ForeignKey(
        NetworkFacility,
        on_delete=models.CASCADE,
        related_name="affiliations",
    )
    role = models.CharField(max_length=32, choices=Role.choices, default=Role.ATTENDING)
    days = models.JSONField(default=list)
    active = models.BooleanField(default=True)

    class Meta:
        db_table = "cymed_eco_provider_directory_practitioner_facility_affiliation"

    def __str__(self) -> str:
        return f"{self.practitioner_id} @ {self.facility_id} ({self.role})"


class DirectoryReview(BaseModel):
    class Kind(models.TextChoices):
        FACILITY = "facility", "Facility"
        PRACTITIONER = "practitioner", "Practitioner"

    class ModerationStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    tenant_id = models.UUIDField(db_index=True)
    kind = models.CharField(max_length=32, choices=Kind.choices, default=Kind.FACILITY)
    facility = models.ForeignKey(
        NetworkFacility,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    practitioner = models.ForeignKey(
        NetworkPractitioner,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    patient_profile_id = models.UUIDField(db_index=True)
    rating = models.IntegerField(default=5)
    text = models.TextField(blank=True)
    posted_at = models.DateTimeField(default=timezone.now)
    moderation_status = models.CharField(
        max_length=32,
        choices=ModerationStatus.choices,
        default=ModerationStatus.PENDING,
    )

    class Meta:
        db_table = "cymed_eco_provider_directory_directory_review"

    def __str__(self) -> str:
        return f"Review {self.pk} ({self.kind}, {self.rating})"
