"""Service layer for prep templates, assignment workflows, and contrast consent."""
from __future__ import annotations

from decimal import Decimal
from typing import Any, Optional

from django.db import transaction
from django.utils import timezone

from .models import ContrastConsent, PrepAssignment, PrepChecklistItem, PrepTemplate


@transaction.atomic
def create_template(
    *,
    code: str,
    title: str,
    title_ar: str = "",
    modality: str,
    body_part: str = "",
    contrast_involved: bool = False,
    fasting_required: bool = False,
    fasting_hours: int = 0,
    hydration_required: bool = False,
    medications_to_hold: Optional[list] = None,
    clothing_instructions: str = "",
    arrive_minutes_before: int = 15,
    what_to_bring: Optional[list] = None,
    body_html: str = "",
    body_html_ar: str = "",
    tenant_id: Optional[Any] = None,
    version: int = 1,
) -> PrepTemplate:
    return PrepTemplate.objects.create(
        tenant_id=tenant_id,
        code=code,
        title=title,
        title_ar=title_ar,
        modality=modality,
        body_part=body_part,
        contrast_involved=contrast_involved,
        fasting_required=fasting_required,
        fasting_hours=fasting_hours,
        hydration_required=hydration_required,
        medications_to_hold=list(medications_to_hold or []),
        clothing_instructions=clothing_instructions,
        arrive_minutes_before=arrive_minutes_before,
        what_to_bring=list(what_to_bring or []),
        body_html=body_html,
        body_html_ar=body_html_ar,
        version=version,
        active=True,
    )


@transaction.atomic
def assign_prep(
    *,
    tenant_id: Any,
    patient_profile_id: Any,
    template_id: Any,
    booking_id: Optional[Any] = None,
    language: str = "en",
) -> PrepAssignment:
    template = PrepTemplate.objects.get(pk=template_id)
    assignment = PrepAssignment.objects.create(
        tenant_id=tenant_id,
        patient_profile_id=patient_profile_id,
        booking_id=booking_id,
        template=template,
        status=PrepAssignment.Status.ASSIGNED,
        language=language,
    )

    position = 0
    seeded: list[PrepChecklistItem] = []

    if template.fasting_required:
        hours = int(template.fasting_hours or 0)
        label = f"Fast for {hours} hours prior to exam" if hours else "Fasting required prior to exam"
        seeded.append(
            PrepChecklistItem(
                assignment=assignment,
                position=position,
                label=label,
                item_kind=PrepChecklistItem.ItemKind.FASTING,
                required=True,
            )
        )
        position += 1

    if template.hydration_required:
        seeded.append(
            PrepChecklistItem(
                assignment=assignment,
                position=position,
                label="Hydrate well before exam",
                item_kind=PrepChecklistItem.ItemKind.HYDRATION,
                required=True,
            )
        )
        position += 1

    for medication in list(template.medications_to_hold or []):
        med_label = str(medication) if not isinstance(medication, dict) else str(medication.get("name") or medication)
        seeded.append(
            PrepChecklistItem(
                assignment=assignment,
                position=position,
                label=f"Hold medication: {med_label}",
                item_kind=PrepChecklistItem.ItemKind.HOLD_MEDICATION,
                required=True,
            )
        )
        position += 1

    for item in list(template.what_to_bring or []):
        bring_label = str(item) if not isinstance(item, dict) else str(item.get("name") or item)
        seeded.append(
            PrepChecklistItem(
                assignment=assignment,
                position=position,
                label=f"Bring: {bring_label}",
                item_kind=PrepChecklistItem.ItemKind.BRING_ITEM,
                required=True,
            )
        )
        position += 1

    arrive_min = int(template.arrive_minutes_before or 0)
    if arrive_min > 0:
        seeded.append(
            PrepChecklistItem(
                assignment=assignment,
                position=position,
                label=f"Arrive {arrive_min} minutes before appointment",
                item_kind=PrepChecklistItem.ItemKind.ARRIVAL_TIME,
                required=True,
            )
        )
        position += 1

    if template.clothing_instructions:
        seeded.append(
            PrepChecklistItem(
                assignment=assignment,
                position=position,
                label=template.clothing_instructions,
                item_kind=PrepChecklistItem.ItemKind.CLOTHING,
                required=True,
            )
        )
        position += 1

    if seeded:
        PrepChecklistItem.objects.bulk_create(seeded)

    return assignment


@transaction.atomic
def mark_item(
    *,
    assignment_id: Any,
    item_id: Any,
    checked: bool,
    note: str = "",
) -> PrepChecklistItem:
    item = PrepChecklistItem.objects.select_for_update().get(
        pk=item_id,
        assignment_id=assignment_id,
    )
    item.checked = bool(checked)
    item.checked_at = timezone.now() if checked else None
    if note:
        item.note = note
    item.save(update_fields=["checked", "checked_at", "note", "updated_at"] if _has_updated_at(item) else ["checked", "checked_at", "note"])

    assignment = PrepAssignment.objects.select_for_update().get(pk=assignment_id)
    required_qs = PrepChecklistItem.objects.filter(assignment_id=assignment_id, required=True)
    total_required = required_qs.count()
    checked_required = required_qs.filter(checked=True).count()

    if total_required > 0 and checked_required == total_required:
        assignment.status = PrepAssignment.Status.CONFIRMED
        assignment.confirmed_at = timezone.now()
    elif checked_required > 0:
        assignment.status = PrepAssignment.Status.PARTIAL
    else:
        if assignment.status == PrepAssignment.Status.CONFIRMED:
            assignment.status = PrepAssignment.Status.PARTIAL
            assignment.confirmed_at = None
    assignment.save()
    return item


@transaction.atomic
def record_view(*, assignment_id: Any) -> PrepAssignment:
    assignment = PrepAssignment.objects.select_for_update().get(pk=assignment_id)
    if assignment.viewed_at is None:
        assignment.viewed_at = timezone.now()
    if assignment.status == PrepAssignment.Status.ASSIGNED:
        assignment.status = PrepAssignment.Status.VIEWED
    assignment.save()
    return assignment


@transaction.atomic
def open_contrast_consent(
    *,
    tenant_id: Any,
    patient_profile_id: Any,
    contrast_kind: str,
    assignment_id: Optional[Any] = None,
) -> ContrastConsent:
    assignment = None
    if assignment_id is not None:
        assignment = PrepAssignment.objects.filter(pk=assignment_id).first()
    return ContrastConsent.objects.create(
        tenant_id=tenant_id,
        patient_profile_id=patient_profile_id,
        assignment=assignment,
        contrast_kind=contrast_kind,
        status=ContrastConsent.Status.PENDING,
    )


@transaction.atomic
def sign_contrast_consent(
    *,
    consent_id: Any,
    signature_url: str,
    witness_profile_id: Optional[Any] = None,
    allergies_reviewed: bool = True,
    egfr_verified: bool = False,
    egfr_value: Optional[Any] = None,
    pregnancy_status: str = "unknown",
) -> ContrastConsent:
    consent = ContrastConsent.objects.select_for_update().get(pk=consent_id)
    consent.signature_url = signature_url or ""
    consent.witness_profile_id = witness_profile_id
    consent.allergies_reviewed = bool(allergies_reviewed)
    consent.egfr_verified = bool(egfr_verified)
    if egfr_value is not None:
        consent.egfr_value = Decimal(str(egfr_value))
    consent.pregnancy_status = pregnancy_status or ContrastConsent.PregnancyStatus.UNKNOWN
    consent.consent_signed_at = timezone.now()
    consent.status = ContrastConsent.Status.SIGNED
    consent.save()
    return consent


@transaction.atomic
def decline_contrast(*, consent_id: Any, reason: str) -> ContrastConsent:
    consent = ContrastConsent.objects.select_for_update().get(pk=consent_id)
    consent.status = ContrastConsent.Status.DECLINED
    consent.decline_reason = reason or ""
    consent.save()
    return consent


def _has_updated_at(instance) -> bool:
    return any(f.name == "updated_at" for f in instance._meta.fields)
