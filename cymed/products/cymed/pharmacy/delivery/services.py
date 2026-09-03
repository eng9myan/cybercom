"""CyMed Pharmacy Delivery business logic."""
from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any, Optional

from django.core.cache import cache
from django.db import transaction
from django.db.models import Avg, Count, Q
from django.utils import timezone


def create_job(**kwargs: Any):
    from .models import DeliveryJob

    with transaction.atomic():
        job = DeliveryJob.objects.create(**kwargs)
    return job


def assign_rider(*, job_id: uuid.UUID | str, rider_id: uuid.UUID | str):
    from .models import DeliveryJob, Rider

    with transaction.atomic():
        job = DeliveryJob.objects.select_for_update().get(pk=job_id)
        rider = Rider.objects.get(pk=rider_id)
        job.rider = rider
        if job.status == DeliveryJob.Status.CREATED:
            job.status = DeliveryJob.Status.ASSIGNED
        job.save(update_fields=["rider", "status", "updated_at"])
        _record_event(job=job, status=job.status, note=f"assigned rider {rider.external_id}")
    return job


def update_status(
    *,
    job_id: uuid.UUID | str,
    status: str,
    lat: Optional[Decimal] = None,
    lng: Optional[Decimal] = None,
    note: str = "",
):
    from .models import DeliveryJob

    with transaction.atomic():
        job = DeliveryJob.objects.select_for_update().get(pk=job_id)
        job.status = status
        job.save(update_fields=["status", "updated_at"])
        _record_event(job=job, status=status, lat=lat, lng=lng, note=note)
    return job


def upload_proof(
    *,
    job_id: uuid.UUID | str,
    photo_url: str = "",
    signature_url: str = "",
    otp_code: Optional[str] = None,
):
    from .models import DeliveryJob

    with transaction.atomic():
        job = DeliveryJob.objects.select_for_update().get(pk=job_id)
        cache_key = f"pod:{job_id}"
        expected = cache.get(cache_key)
        otp_verified = False
        if otp_code is not None and expected is not None and str(expected) == str(otp_code):
            otp_verified = True
            cache.delete(cache_key)
        job.proof_of_delivery = {
            "photo_url": photo_url,
            "signature_url": signature_url,
            "otp_verified": otp_verified,
            "captured_at": timezone.now().isoformat(),
        }
        if otp_verified:
            job.status = DeliveryJob.Status.DELIVERED
            job.save(update_fields=["proof_of_delivery", "status", "updated_at"])
            _record_event(job=job, status=job.status, note="POD uploaded with OTP")
        else:
            job.save(update_fields=["proof_of_delivery", "updated_at"])
            _record_event(job=job, status=job.status, note="POD uploaded (no OTP verify)")
    return job


def dispatch_to_provider(job_id: uuid.UUID | str) -> str:
    from .models import DeliveryJob

    job = DeliveryJob.objects.select_related("courier").get(pk=job_id)
    provider = job.courier.provider
    handler = _PROVIDER_HANDLERS.get(provider, _dispatch_other)
    tracking_id = handler(job)
    job.courier_tracking_id = tracking_id
    job.save(update_fields=["courier_tracking_id", "updated_at"])
    return tracking_id


def kpi_snapshot(tenant_id: uuid.UUID | str) -> dict:
    from .models import DeliveryJob

    qs = DeliveryJob.objects.filter(tenant_id=tenant_id)
    total = qs.count()
    delivered = qs.filter(status=DeliveryJob.Status.DELIVERED).count()
    failed = qs.filter(status=DeliveryJob.Status.FAILED).count()
    in_transit = qs.filter(status=DeliveryJob.Status.IN_TRANSIT).count()
    cold = qs.filter(cold_chain_required=True).count()
    avg_cost = qs.aggregate(v=Avg("cost")).get("v") or Decimal("0")
    on_time = qs.filter(
        status=DeliveryJob.Status.DELIVERED,
        estimated_arrival__isnull=False,
    ).count()
    return {
        "total_jobs": total,
        "delivered": delivered,
        "failed": failed,
        "in_transit": in_transit,
        "cold_chain_jobs": cold,
        "on_time_delivered": on_time,
        "avg_cost": str(avg_cost),
        "success_rate": (delivered / total) if total else 0.0,
    }


def _record_event(
    *,
    job,
    status: str,
    lat: Optional[Decimal] = None,
    lng: Optional[Decimal] = None,
    note: str = "",
):
    from .models import DeliveryStatusEvent

    DeliveryStatusEvent.objects.create(
        job=job,
        status=status,
        lat=lat,
        lng=lng,
        note=note,
    )


def _dispatch_internal(job) -> str:
    return f"INT-{job.pk}"


def _dispatch_aramex(job) -> str:
    return f"ARX-{uuid.uuid4().hex[:12].upper()}"


def _dispatch_dhl(job) -> str:
    return f"DHL-{uuid.uuid4().hex[:12].upper()}"


def _dispatch_naqel(job) -> str:
    return f"NQL-{uuid.uuid4().hex[:12].upper()}"


def _dispatch_smsa(job) -> str:
    return f"SMSA-{uuid.uuid4().hex[:12].upper()}"


def _dispatch_mrsool(job) -> str:
    return f"MRS-{uuid.uuid4().hex[:12].upper()}"


def _dispatch_careem(job) -> str:
    return f"CRM-{uuid.uuid4().hex[:12].upper()}"


def _dispatch_other(job) -> str:
    return f"OTH-{uuid.uuid4().hex[:12].upper()}"


_PROVIDER_HANDLERS = {
    "internal": _dispatch_internal,
    "aramex": _dispatch_aramex,
    "dhl": _dispatch_dhl,
    "naqel": _dispatch_naqel,
    "smsa": _dispatch_smsa,
    "mrsool": _dispatch_mrsool,
    "careem": _dispatch_careem,
    "other": _dispatch_other,
}
