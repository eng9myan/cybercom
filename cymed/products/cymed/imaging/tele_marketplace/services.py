"""Service functions for teleradiology marketplace workflows."""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from django.db import transaction
from django.utils import timezone

from .models import Bid, RadiologistProvider, ReadContract, TeleReadJob, TeleReport


_SLA_PRIORITY_MINUTES = {
    "stat": 30,
    "urgent": 120,
    "routine": 720,
}


@transaction.atomic
def onboard_provider(
    *,
    display_name: str,
    organization: str = "",
    country: str = "",
    licenses: list[dict[str, Any]],
    modalities: list[str],
    body_parts: list[str] | None = None,
    subspecialty: list[str] | None = None,
    languages: list[str] | None = None,
    tier: str = "general",
    hourly_rate: Decimal | float | int | str | None = None,
    per_study_rate: Decimal | float | int | str | None = None,
    tenant_id: Any = None,
) -> RadiologistProvider:
    provider = RadiologistProvider.objects.create(
        tenant_id=tenant_id,
        display_name=display_name,
        organization=organization,
        country=country,
        licenses=list(licenses or []),
        modalities=list(modalities or []),
        body_parts=list(body_parts or []),
        subspecialty=list(subspecialty or []),
        languages=list(languages or []),
        tier=tier,
        hourly_rate=Decimal(str(hourly_rate)) if hourly_rate is not None else None,
        per_study_rate=Decimal(str(per_study_rate)) if per_study_rate is not None else None,
    )
    return provider


@transaction.atomic
def sign_contract(
    *,
    tenant_id: Any,
    provider_id: Any,
    start_date: Any,
    payment_terms: str,
    payment_amount: Decimal | float | int | str | None,
    modalities: list[str],
    nda_signed: bool = False,
    insurance_verified: bool = False,
) -> ReadContract:
    provider = RadiologistProvider.objects.get(pk=provider_id)
    contract = ReadContract.objects.create(
        tenant_id=tenant_id,
        provider=provider,
        start_date=start_date,
        payment_terms=payment_terms,
        payment_amount=(
            Decimal(str(payment_amount)) if payment_amount is not None else None
        ),
        modalities=list(modalities or []),
        nda_signed=bool(nda_signed),
        liability_insurance_verified=bool(insurance_verified),
        status=ReadContract.Status.ACTIVE,
    )
    return contract


@transaction.atomic
def post_job(
    *,
    tenant_id: Any,
    study_instance_uid: str,
    modality: str,
    body_part: str = "",
    priority: str = "routine",
    patient_profile_id: Any = None,
    ordered_by_profile_id: Any = None,
    direct_assign_provider_id: Any = None,
) -> TeleReadJob:
    sla_minutes = _SLA_PRIORITY_MINUTES.get(priority, _SLA_PRIORITY_MINUTES["routine"])
    now = timezone.now()
    sla_deadline_at: datetime = now + timedelta(minutes=sla_minutes)

    assigned_provider = None
    status = TeleReadJob.Status.BIDS_OPEN
    assigned_at = None
    if direct_assign_provider_id:
        assigned_provider = RadiologistProvider.objects.get(pk=direct_assign_provider_id)
        status = TeleReadJob.Status.ASSIGNED
        assigned_at = now

    job = TeleReadJob.objects.create(
        tenant_id=tenant_id,
        study_instance_uid=study_instance_uid,
        ordered_by_profile_id=ordered_by_profile_id,
        patient_profile_id=patient_profile_id,
        modality=modality,
        body_part=body_part,
        priority=priority,
        assigned_provider=assigned_provider,
        status=status,
        requested_at=now,
        assigned_at=assigned_at,
        sla_deadline_at=sla_deadline_at,
    )
    return job


@transaction.atomic
def submit_bid(
    *,
    job_id: Any,
    provider_id: Any,
    amount: Decimal | float | int | str,
    eta_minutes: int,
    note: str = "",
) -> Bid:
    job = TeleReadJob.objects.get(pk=job_id)
    provider = RadiologistProvider.objects.get(pk=provider_id)
    bid = Bid.objects.create(
        tenant_id=job.tenant_id,
        job=job,
        provider=provider,
        amount=Decimal(str(amount)),
        eta_minutes=int(eta_minutes),
        note=note,
        status=Bid.Status.SUBMITTED,
    )
    if job.status == TeleReadJob.Status.POSTED:
        job.status = TeleReadJob.Status.BIDS_OPEN
        job.save(update_fields=["status", "updated_at"])
    return bid


@transaction.atomic
def accept_bid(*, bid_id: Any) -> TeleReadJob:
    bid = Bid.objects.select_related("job", "provider").get(pk=bid_id)
    job = bid.job
    now = timezone.now()

    Bid.objects.filter(job=job, status=Bid.Status.SUBMITTED).exclude(pk=bid.pk).update(
        status=Bid.Status.REJECTED
    )

    bid.status = Bid.Status.ACCEPTED
    bid.save(update_fields=["status", "updated_at"])

    job.assigned_provider = bid.provider
    job.payout_amount = bid.amount
    job.currency = bid.currency
    job.status = TeleReadJob.Status.ASSIGNED
    job.assigned_at = now
    job.save(
        update_fields=[
            "assigned_provider",
            "payout_amount",
            "currency",
            "status",
            "assigned_at",
            "updated_at",
        ]
    )
    return job


@transaction.atomic
def submit_report(
    *,
    job_id: Any,
    provider_id: Any,
    kind: str = "preliminary",
    text: str = "",
    findings: dict[str, Any] | None = None,
    impressions: str = "",
    signed: bool = False,
) -> TeleReport:
    job = TeleReadJob.objects.get(pk=job_id)
    provider = RadiologistProvider.objects.get(pk=provider_id) if provider_id else None

    last_version = (
        TeleReport.objects.filter(job=job).order_by("-version").values_list("version", flat=True).first()
    )
    next_version = (last_version or 0) + 1

    now = timezone.now()
    report = TeleReport.objects.create(
        tenant_id=job.tenant_id,
        job=job,
        version=next_version,
        kind=kind,
        text=text,
        findings=dict(findings or {}),
        impressions=impressions,
        submitted_by_provider=provider,
        submitted_at=now,
        signed=bool(signed),
    )

    if kind == TeleReport.Kind.FINAL and signed:
        job.status = TeleReadJob.Status.FINAL_REPORT
        job.final_at = now
        job.save(update_fields=["status", "final_at", "updated_at"])
    elif kind == TeleReport.Kind.PRELIMINARY:
        job.status = TeleReadJob.Status.DRAFT_REPORT
        job.draft_at = now
        job.save(update_fields=["status", "draft_at", "updated_at"])
    return report


@transaction.atomic
def finalize_job(*, job_id: Any) -> TeleReadJob:
    job = TeleReadJob.objects.get(pk=job_id)
    now = timezone.now()
    if job.final_at is None:
        job.final_at = now
    job.status = TeleReadJob.Status.COMPLETED
    job.save(update_fields=["status", "final_at", "updated_at"])
    return job


@transaction.atomic
def dispute_job(*, job_id: Any, reason: str) -> TeleReadJob:
    job = TeleReadJob.objects.get(pk=job_id)
    job.status = TeleReadJob.Status.DISPUTED
    job.save(update_fields=["status", "updated_at"])
    TeleReport.objects.create(
        tenant_id=job.tenant_id,
        job=job,
        version=(
            (TeleReport.objects.filter(job=job).order_by("-version").values_list("version", flat=True).first() or 0)
            + 1
        ),
        kind=TeleReport.Kind.ADDENDUM,
        text=f"DISPUTE: {reason}",
        impressions="",
        signed=False,
    )
    return job
