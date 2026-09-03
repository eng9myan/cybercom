"""Service layer for credentialing workflows and license verification."""
from __future__ import annotations

from typing import Any

from django.db import transaction
from django.utils import timezone

from .models import (
    CredentialDocument,
    CredentialingApplication,
    LicenseVerification,
    PrivilegeGrant,
)


@transaction.atomic
def open_application(
    *,
    tenant_id: Any,
    subject_kind: str,
    facility_id: Any = None,
    practitioner_id: Any = None,
    submitted_by_profile_id: Any = None,
    target_networks: list | None = None,
) -> CredentialingApplication:
    app = CredentialingApplication.objects.create(
        tenant_id=tenant_id,
        subject_kind=subject_kind,
        facility_id=facility_id,
        practitioner_id=practitioner_id,
        submitted_by_profile_id=submitted_by_profile_id,
        target_networks=list(target_networks or []),
        status=CredentialingApplication.Status.SUBMITTED,
        submitted_at=timezone.now(),
    )
    return app


@transaction.atomic
def upload_document(
    *,
    application_id: Any,
    kind: str,
    file_url: str,
    expires_at: Any = None,
) -> CredentialDocument:
    doc = CredentialDocument.objects.create(
        application_id=application_id,
        kind=kind,
        file_url=file_url,
        expires_at=expires_at,
        verification_status=CredentialDocument.VerificationStatus.PENDING,
    )
    return doc


@transaction.atomic
def verify_license(
    *,
    document_id: Any = None,
    issuing_authority: str,
    license_number: str,
    jurisdiction: str,
    verification_kind: str = "automated_registry",
    raw_response: dict | None = None,
) -> LicenseVerification:
    if verification_kind == LicenseVerification.VerificationKind.AUTOMATED_REGISTRY:
        result = LicenseVerification.Result.VERIFIED
        response_payload = raw_response if raw_response is not None else {"source": "stub"}
    else:
        result = LicenseVerification.Result.PENDING
        response_payload = raw_response if raw_response is not None else {}

    verification = LicenseVerification.objects.create(
        document_id=document_id,
        issuing_authority=issuing_authority,
        license_number=license_number,
        jurisdiction=jurisdiction,
        verification_kind=verification_kind,
        at=timezone.now(),
        result=result,
        raw_response=response_payload,
    )

    if document_id and result == LicenseVerification.Result.VERIFIED:
        CredentialDocument.objects.filter(pk=document_id).update(
            verification_status=CredentialDocument.VerificationStatus.VERIFIED,
            verified_at=timezone.now(),
            verification_reference=license_number,
        )

    return verification


@transaction.atomic
def request_more_info(*, application_id: Any, note: str) -> CredentialingApplication:
    app = CredentialingApplication.objects.select_for_update().get(pk=application_id)
    app.status = CredentialingApplication.Status.INFO_REQUESTED
    app.decision_reason = note
    app.save(update_fields=["status", "decision_reason", "updated_at"])
    return app


@transaction.atomic
def approve_application(
    *,
    application_id: Any,
    decided_by_profile_id: Any,
    decision_reason: str = "",
    expires_at: Any = None,
) -> CredentialingApplication:
    app = CredentialingApplication.objects.select_for_update().get(pk=application_id)
    unverified = app.documents.exclude(
        verification_status=CredentialDocument.VerificationStatus.VERIFIED
    ).exists()
    if unverified:
        raise ValueError("All credential documents must be verified before approval.")
    app.status = CredentialingApplication.Status.APPROVED
    app.decided_at = timezone.now()
    app.decision_reason = decision_reason
    app.expires_at = expires_at
    app.save(update_fields=["status", "decided_at", "decision_reason", "expires_at", "updated_at"])
    return app


@transaction.atomic
def reject_application(*, application_id: Any, decision_reason: str) -> CredentialingApplication:
    app = CredentialingApplication.objects.select_for_update().get(pk=application_id)
    app.status = CredentialingApplication.Status.REJECTED
    app.decided_at = timezone.now()
    app.decision_reason = decision_reason
    app.save(update_fields=["status", "decided_at", "decision_reason", "updated_at"])
    return app


@transaction.atomic
def grant_privileges(
    *,
    application_id: Any,
    tenant_id: Any,
    subject_kind: str,
    facility_id: Any = None,
    practitioner_id: Any = None,
    privilege_scope: list,
    granted_by_profile_id: Any,
    expires_at: Any = None,
) -> PrivilegeGrant:
    grant = PrivilegeGrant.objects.create(
        application_id=application_id,
        tenant_id=tenant_id,
        subject_kind=subject_kind,
        facility_id=facility_id,
        practitioner_id=practitioner_id,
        privilege_scope=list(privilege_scope or []),
        granted_by_profile_id=granted_by_profile_id,
        granted_at=timezone.now(),
        expires_at=expires_at,
        status=PrivilegeGrant.Status.ACTIVE,
    )
    return grant


@transaction.atomic
def revoke_privileges(*, grant_id: Any, reason: str) -> PrivilegeGrant:
    grant = PrivilegeGrant.objects.select_for_update().get(pk=grant_id)
    grant.status = PrivilegeGrant.Status.REVOKED
    grant.save(update_fields=["status", "updated_at"])
    return grant
