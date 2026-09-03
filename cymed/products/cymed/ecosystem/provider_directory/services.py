"""Service functions for the provider directory sub-app."""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from django.db import transaction
from django.db.models import Avg, Count, Q

from .models import (
    DirectoryReview,
    NetworkFacility,
    NetworkPractitioner,
    PractitionerFacilityAffiliation,
)


@transaction.atomic
def register_facility(**kwargs: Any) -> NetworkFacility:
    return NetworkFacility.objects.create(**kwargs)


@transaction.atomic
def register_practitioner(**kwargs: Any) -> NetworkPractitioner:
    return NetworkPractitioner.objects.create(**kwargs)


@transaction.atomic
def affiliate(
    *,
    practitioner_id: Any,
    facility_id: Any,
    role: str = "attending",
    days: list | None = None,
) -> PractitionerFacilityAffiliation:
    return PractitionerFacilityAffiliation.objects.create(
        practitioner_id=practitioner_id,
        facility_id=facility_id,
        role=role,
        days=list(days or []),
    )


def search_facilities(
    *,
    kind: str | None = None,
    city: str | None = None,
    country: str | None = None,
    specialty: str | None = None,
    insurer: str | None = None,
    telehealth: bool | None = None,
    home_visit: bool | None = None,
    min_rating: float | int | str = 0,
):
    qs = NetworkFacility.objects.filter(active=True)
    if kind:
        qs = qs.filter(kind=kind)
    if city:
        qs = qs.filter(city__iexact=city)
    if country:
        qs = qs.filter(country__iexact=country)
    if specialty:
        qs = qs.filter(specialties__contains=[specialty])
    if insurer:
        qs = qs.filter(accepts_insurers__contains=[insurer])
    if telehealth is not None:
        qs = qs.filter(telehealth_capable=bool(telehealth))
    if home_visit is not None:
        qs = qs.filter(home_visit_capable=bool(home_visit))
    try:
        threshold = Decimal(str(min_rating))
    except Exception:
        threshold = Decimal("0")
    if threshold > 0:
        qs = qs.filter(rating__gte=threshold)
    return qs.order_by("-rating", "name")


def search_practitioners(
    *,
    specialty: str | None = None,
    facility_id: Any = None,
    language: str | None = None,
    teleconsult: bool | None = None,
    min_rating: float | int | str = 0,
    accepts_new: bool | None = None,
):
    qs = NetworkPractitioner.objects.filter(active=True)
    if specialty:
        qs = qs.filter(specialty__iexact=specialty)
    if facility_id:
        qs = qs.filter(
            Q(primary_facility_id=facility_id)
            | Q(affiliations__facility_id=facility_id, affiliations__active=True)
        ).distinct()
    if language:
        qs = qs.filter(languages__contains=[language])
    if teleconsult is not None:
        qs = qs.filter(teleconsultation_capable=bool(teleconsult))
    if accepts_new is not None:
        qs = qs.filter(accepts_new_patients=bool(accepts_new))
    try:
        threshold = Decimal(str(min_rating))
    except Exception:
        threshold = Decimal("0")
    if threshold > 0:
        qs = qs.filter(rating__gte=threshold)
    return qs.order_by("-rating", "last_name", "first_name")


@transaction.atomic
def post_review(
    *,
    tenant_id: Any,
    kind: str,
    facility_id: Any = None,
    practitioner_id: Any = None,
    patient_profile_id: Any,
    rating: int,
    text: str = "",
) -> DirectoryReview:
    review = DirectoryReview.objects.create(
        tenant_id=tenant_id,
        kind=kind,
        facility_id=facility_id,
        practitioner_id=practitioner_id,
        patient_profile_id=patient_profile_id,
        rating=int(rating),
        text=text,
        moderation_status=DirectoryReview.ModerationStatus.PENDING,
    )
    return review


@transaction.atomic
def moderate_review(*, review_id: Any, approve: bool, reason: str = "") -> DirectoryReview:
    review = DirectoryReview.objects.select_for_update().get(pk=review_id)
    if approve:
        review.moderation_status = DirectoryReview.ModerationStatus.APPROVED
    else:
        review.moderation_status = DirectoryReview.ModerationStatus.REJECTED
        if reason:
            review.text = (review.text or "") + f"\n[rejected: {reason}]"
    review.save(update_fields=["moderation_status", "text", "updated_at"] if hasattr(review, "updated_at") else ["moderation_status", "text"])
    if approve:
        _recompute_target_rating(review)
    return review


def _recompute_target_rating(review: DirectoryReview) -> None:
    approved = DirectoryReview.objects.filter(
        moderation_status=DirectoryReview.ModerationStatus.APPROVED,
        kind=review.kind,
    )
    if review.kind == DirectoryReview.Kind.FACILITY and review.facility_id:
        stats = approved.filter(facility_id=review.facility_id).aggregate(
            avg=Avg("rating"), total=Count("id")
        )
        NetworkFacility.objects.filter(pk=review.facility_id).update(
            rating=Decimal(str(round(stats["avg"] or 0, 2))),
            review_count=int(stats["total"] or 0),
        )
    elif review.kind == DirectoryReview.Kind.PRACTITIONER and review.practitioner_id:
        stats = approved.filter(practitioner_id=review.practitioner_id).aggregate(
            avg=Avg("rating"), total=Count("id")
        )
        NetworkPractitioner.objects.filter(pk=review.practitioner_id).update(
            rating=Decimal(str(round(stats["avg"] or 0, 2))),
            review_count=int(stats["total"] or 0),
        )
