"""Business services for shared inventory/capacity marketplace and provider pools."""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from .models import (
    RadiologistPoolShift,
    ResourceMatch,
    ResourceOffer,
    ResourceRequest,
)


def post_offer(
    *,
    tenant_id: Any,
    kind: str,
    quantity: Decimal,
    uom: str = "",
    code: str = "",
    description: str = "",
    start_at: Any = None,
    end_at: Any = None,
    location: dict | None = None,
    price_per_unit: Decimal | None = None,
    currency: str = "SAR",
    tags: list | None = None,
    visible_to_tenant_ids: list | None = None,
) -> ResourceOffer:
    return ResourceOffer.objects.create(
        tenant_id=tenant_id,
        kind=kind,
        code=code,
        description=description,
        quantity=Decimal(str(quantity)),
        uom=uom,
        start_at=start_at,
        end_at=end_at,
        location=location or {},
        price_per_unit=price_per_unit,
        currency=currency,
        tags=tags or [],
        visible_to_tenant_ids=visible_to_tenant_ids or [],
        status=ResourceOffer.Status.OPEN,
        posted_at=timezone.now(),
    )


def post_request(
    *,
    tenant_id: Any,
    kind: str,
    quantity_needed: Decimal,
    uom: str = "",
    code: str = "",
    description: str = "",
    needed_by: Any = None,
    max_price_per_unit: Decimal | None = None,
    currency: str = "SAR",
    location: dict | None = None,
    urgency: str = "routine",
) -> ResourceRequest:
    return ResourceRequest.objects.create(
        tenant_id=tenant_id,
        kind=kind,
        code=code,
        description=description,
        quantity_needed=Decimal(str(quantity_needed)),
        uom=uom,
        needed_by=needed_by,
        max_price_per_unit=max_price_per_unit,
        currency=currency,
        location=location or {},
        urgency=urgency,
        status=ResourceRequest.Status.OPEN,
        posted_at=timezone.now(),
    )


@transaction.atomic
def match_request(*, request_id: Any) -> list[ResourceMatch]:
    request = ResourceRequest.objects.select_for_update().get(pk=request_id)
    if request.status != ResourceRequest.Status.OPEN:
        return list(request.matches.all())

    offers_qs = ResourceOffer.objects.select_for_update().filter(
        kind=request.kind,
        status__in=[
            ResourceOffer.Status.OPEN,
            ResourceOffer.Status.PARTIALLY_TAKEN,
        ],
        quantity__gt=Decimal("0"),
    )

    if request.max_price_per_unit is not None:
        offers_qs = offers_qs.filter(
            Q(price_per_unit__lte=request.max_price_per_unit)
            | Q(price_per_unit__isnull=True)
        )

    if request.needed_by is not None:
        offers_qs = offers_qs.filter(
            Q(end_at__isnull=True) | Q(end_at__gte=request.needed_by)
        )

    matches: list[ResourceMatch] = []
    remaining = Decimal(str(request.quantity_needed))

    for offer in offers_qs.order_by("posted_at"):
        if remaining <= Decimal("0"):
            break
        visible = offer.visible_to_tenant_ids or []
        if visible and str(request.tenant_id) not in {str(t) for t in visible}:
            continue
        available = Decimal(str(offer.quantity))
        if available <= Decimal("0"):
            continue
        take = available if available < remaining else remaining
        price = offer.price_per_unit
        total = (price * take) if price is not None else Decimal("0")
        match = ResourceMatch.objects.create(
            tenant_id=request.tenant_id,
            offer=offer,
            request=request,
            quantity=take,
            agreed_price_per_unit=price,
            currency=offer.currency,
            total_amount=total,
            status=ResourceMatch.Status.PROPOSED,
            created_at_ts=timezone.now(),
        )
        matches.append(match)
        remaining -= take

    return matches


@transaction.atomic
def accept_match(*, match_id: Any) -> ResourceMatch:
    match = ResourceMatch.objects.select_for_update().get(pk=match_id)
    if match.status != ResourceMatch.Status.PROPOSED:
        return match

    offer = ResourceOffer.objects.select_for_update().get(pk=match.offer_id)
    request = ResourceRequest.objects.select_for_update().get(pk=match.request_id)

    take = Decimal(str(match.quantity))
    available = Decimal(str(offer.quantity))
    if take > available:
        take = available
        match.quantity = take
        if match.agreed_price_per_unit is not None:
            match.total_amount = match.agreed_price_per_unit * take

    new_qty = available - take
    offer.quantity = new_qty
    if new_qty <= Decimal("0"):
        offer.status = ResourceOffer.Status.CLOSED
    else:
        offer.status = ResourceOffer.Status.PARTIALLY_TAKEN
    offer.save(update_fields=["quantity", "status", "updated_at"])

    request.matched_offer = offer
    request.status = ResourceRequest.Status.MATCHED
    request.save(update_fields=["matched_offer", "status", "updated_at"])

    match.status = ResourceMatch.Status.ACCEPTED
    match.accepted_at = timezone.now()
    match.save(update_fields=["quantity", "total_amount", "status", "accepted_at", "updated_at"])
    return match


@transaction.atomic
def decline_match(*, match_id: Any, reason: str = "") -> ResourceMatch:
    match = ResourceMatch.objects.select_for_update().get(pk=match_id)
    if match.status not in {ResourceMatch.Status.PROPOSED, ResourceMatch.Status.ACCEPTED}:
        return match
    match.status = ResourceMatch.Status.DECLINED
    match.decline_reason = reason
    match.save(update_fields=["status", "decline_reason", "updated_at"])
    return match


@transaction.atomic
def fulfill_match(*, match_id: Any) -> ResourceMatch:
    match = ResourceMatch.objects.select_for_update().get(pk=match_id)
    if match.status not in {ResourceMatch.Status.ACCEPTED, ResourceMatch.Status.PROPOSED}:
        return match
    match.status = ResourceMatch.Status.FULFILLED
    match.fulfilled_at = timezone.now()
    match.save(update_fields=["status", "fulfilled_at", "updated_at"])

    request = ResourceRequest.objects.select_for_update().get(pk=match.request_id)
    request.status = ResourceRequest.Status.FULFILLED
    request.save(update_fields=["status", "updated_at"])
    return match


def post_radiologist_shift(
    *,
    tenant_id: Any,
    provider_id: Any,
    date: Any,
    start_time: Any,
    end_time: Any,
    modalities: list,
    max_studies: int,
) -> RadiologistPoolShift:
    return RadiologistPoolShift.objects.create(
        tenant_id=tenant_id,
        provider_id=provider_id,
        date=date,
        start_time=start_time,
        end_time=end_time,
        modalities=list(modalities or []),
        max_studies=int(max_studies),
        accepted_studies=0,
        status=RadiologistPoolShift.Status.OPEN,
    )


@transaction.atomic
def increment_shift_load(*, shift_id: Any, n: int = 1) -> RadiologistPoolShift:
    shift = RadiologistPoolShift.objects.select_for_update().get(pk=shift_id)
    shift.accepted_studies = int(shift.accepted_studies) + int(n)
    if shift.max_studies > 0 and shift.accepted_studies >= shift.max_studies:
        shift.status = RadiologistPoolShift.Status.FULL
    elif shift.accepted_studies > 0:
        shift.status = RadiologistPoolShift.Status.PARTIALLY_FULL
    shift.save(update_fields=["accepted_studies", "status", "updated_at"])
    return shift
