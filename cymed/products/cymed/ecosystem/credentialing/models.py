"""Domain models for CyMed provider credentialing and license verification."""
from __future__ import annotations

import uuid
from decimal import Decimal

from django.db import models
from django.utils import timezone

from platform.common.models import BaseModel


class CredentialingApplication(BaseModel):
    class SubjectKind(models.TextChoices):
        FACILITY = "facility", "Facility"
        PRACTITIONER = "practitioner", "Practitioner"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SUBMITTED = "submitted", "Submitted"
        UNDER_REVIEW = "under_review", "Under Review"
        INFO_REQUESTED = "info_requested", "Info Requested"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        SUSPENDED = "suspended", "Suspended"
        RENEWED = "renewed", "Renewed"

    tenant_id = models.UUIDField(db_index=True)
    subject_kind = models.CharField(max_length=32, choices=SubjectKind.choices)
    facility_id = models.UUIDField(null=True, blank=True)
    practitioner_id = models.UUIDField(null=True, blank=True)
    submitted_by_profile_id = models.UUIDField(null=True, blank=True)
    target_networks = models.JSONField(default=list, blank=True)
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    decision_reason = models.TextField(blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cymed_eco_credentialing_credentialing_application"

    def __str__(self) -> str:
        return f"CredentialingApplication({self.subject_kind}:{self.status})"


class CredentialDocument(BaseModel):
    class Kind(models.TextChoices):
        MEDICAL_LICENSE = "medical_license", "Medical License"
        DEA_LICENSE = "dea_license", "DEA License"
        MALPRACTICE_INSURANCE = "malpractice_insurance", "Malpractice Insurance"
        BOARD_CERTIFICATION = "board_certification", "Board Certification"
        MEDICAL_SCHOOL_DIPLOMA = "medical_school_diploma", "Medical School Diploma"
        CME_CERTIFICATE = "cme_certificate", "CME Certificate"
        PASSPORT = "passport", "Passport"
        NATIONAL_ID = "national_id", "National ID"
        CV = "cv", "CV"
        ACCREDITATION = "accreditation", "Accreditation"
        OTHER = "other", "Other"

    class VerificationStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        VERIFIED = "verified", "Verified"
        REJECTED = "rejected", "Rejected"
        EXPIRED = "expired", "Expired"

    application = models.ForeignKey(
        CredentialingApplication,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    kind = models.CharField(max_length=32, choices=Kind.choices)
    file_url = models.URLField(blank=True)
    uploaded_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(null=True, blank=True)
    verification_status = models.CharField(
        max_length=32,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
    )
    verified_by_profile_id = models.UUIDField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verification_reference = models.CharField(max_length=255, blank=True)
    note = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_eco_credentialing_credential_document"

    def __str__(self) -> str:
        return f"CredentialDocument({self.kind}:{self.verification_status})"


class LicenseVerification(BaseModel):
    class VerificationKind(models.TextChoices):
        AUTOMATED_REGISTRY = "automated_registry", "Automated Registry"
        MANUAL_EMAIL = "manual_email", "Manual Email"
        PRIMARY_SOURCE = "primary_source", "Primary Source"
        SELF_ATTEST = "self_attest", "Self Attest"

    class Result(models.TextChoices):
        VERIFIED = "verified", "Verified"
        NOT_FOUND = "not_found", "Not Found"
        EXPIRED = "expired", "Expired"
        SUSPENDED = "suspended", "Suspended"
        PENDING = "pending", "Pending"

    document = models.ForeignKey(
        CredentialDocument,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="verifications",
    )
    issuing_authority = models.CharField(max_length=255, blank=True)
    license_number = models.CharField(max_length=128, blank=True)
    jurisdiction = models.CharField(max_length=64, blank=True)
    verification_kind = models.CharField(
        max_length=32,
        choices=VerificationKind.choices,
        default=VerificationKind.AUTOMATED_REGISTRY,
    )
    at = models.DateTimeField(default=timezone.now)
    result = models.CharField(
        max_length=32,
        choices=Result.choices,
        default=Result.PENDING,
    )
    raw_response = models.JSONField(default=dict, blank=True)
    note = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_eco_credentialing_license_verification"

    def __str__(self) -> str:
        return f"LicenseVerification({self.issuing_authority}:{self.result})"


class PrivilegeGrant(BaseModel):
    class SubjectKind(models.TextChoices):
        FACILITY = "facility", "Facility"
        PRACTITIONER = "practitioner", "Practitioner"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        REVOKED = "revoked", "Revoked"
        EXPIRED = "expired", "Expired"
        SUSPENDED = "suspended", "Suspended"

    application = models.ForeignKey(
        CredentialingApplication,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="privilege_grants",
    )
    tenant_id = models.UUIDField(db_index=True)
    subject_kind = models.CharField(max_length=32, choices=SubjectKind.choices)
    facility_id = models.UUIDField(null=True, blank=True)
    practitioner_id = models.UUIDField(null=True, blank=True)
    privilege_scope = models.JSONField(default=list, blank=True)
    granted_by_profile_id = models.UUIDField(null=True, blank=True)
    granted_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    class Meta:
        db_table = "cymed_eco_credentialing_privilege_grant"

    def __str__(self) -> str:
        return f"PrivilegeGrant({self.subject_kind}:{self.status})"
