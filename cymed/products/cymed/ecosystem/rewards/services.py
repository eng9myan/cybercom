"""Business services for CyMed ecosystem-wide loyalty program."""
from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Optional

from django.db import transaction

from .models import (
    EcosystemAccount,
    EcosystemPointsEvent,
    EcosystemProgram,
    EcosystemRedemption,
    EcosystemReward,
)


def _recompute_tier(account: EcosystemAccount) -> None:
    tiers = account.program.tiers.all().order_by("-threshold_points")
    for tier in tiers:
        if account.lifetime_points >= tier.threshold_points:
            if account.current_tier != tier.code:
                account.current_tier = tier.code
                account.save(update_fields=["current_tier"])
            return
    if account.current_tier:
        account.current_tier = ""
        account.save(update_fields=["current_tier"])


@transaction.atomic
def enroll(*, program_id, patient_profile_id, primary_country: str = "") -> EcosystemAccount:
    program = EcosystemProgram.objects.get(pk=program_id)
    account, _created = EcosystemAccount.objects.get_or_create(
        program=program,
        patient_profile_id=patient_profile_id,
        defaults={"primary_country": primary_country},
    )
    _recompute_tier(account)
    return account


@transaction.atomic
def earn(
    *,
    account_id,
    source_tenant_id,
    currency_amount: Decimal,
    reference_kind: str,
    reference_id,
    reason: str = "",
) -> EcosystemPointsEvent:
    account = EcosystemAccount.objects.select_for_update().get(pk=account_id)
    program = account.program
    points = int((Decimal(currency_amount) * Decimal(program.currency_conversion)).to_integral_value())
    event = EcosystemPointsEvent.objects.create(
        account=account,
        kind=EcosystemPointsEvent.Kind.EARN,
        points=points,
        source_tenant_id=source_tenant_id,
        reference_kind=reference_kind,
        reference_id=reference_id,
        reason=reason,
    )
    account.balance_points = account.balance_points + points
    account.lifetime_points = account.lifetime_points + points
    account.save(update_fields=["balance_points", "lifetime_points"])
    _recompute_tier(account)
    return event


@transaction.atomic
def redeem(*, account_id, reward_id, redeemed_at_tenant_id) -> EcosystemRedemption:
    account = EcosystemAccount.objects.select_for_update().get(pk=account_id)
    reward = EcosystemReward.objects.select_for_update().get(pk=reward_id)
    if not reward.active:
        raise ValueError("reward_inactive")
    if reward.program_id != account.program_id:
        raise ValueError("reward_program_mismatch")
    if account.balance_points < reward.cost_points:
        raise ValueError("insufficient_points")
    allowed_tenants = list(reward.redeemable_at_tenant_ids or [])
    if allowed_tenants and redeemed_at_tenant_id is not None:
        if str(redeemed_at_tenant_id) not in [str(t) for t in allowed_tenants]:
            raise ValueError("tenant_not_allowed")
    if reward.stock_left == 0:
        raise ValueError("out_of_stock")
    if reward.stock_left > 0:
        reward.stock_left = reward.stock_left - 1
        reward.save(update_fields=["stock_left"])
    account.balance_points = account.balance_points - reward.cost_points
    account.save(update_fields=["balance_points"])
    EcosystemPointsEvent.objects.create(
        account=account,
        kind=EcosystemPointsEvent.Kind.REDEEM,
        points=-reward.cost_points,
        source_tenant_id=redeemed_at_tenant_id,
        reference_kind="reward",
        reference_id=reward.id if hasattr(reward, "id") else None,
        reason=f"redeem:{reward.code}",
    )
    redemption = EcosystemRedemption.objects.create(
        account=account,
        reward=reward,
        points_spent=reward.cost_points,
        code=uuid.uuid4().hex[:16].upper(),
        redeemed_at_tenant_id=redeemed_at_tenant_id,
        status=EcosystemRedemption.Status.ISSUED,
    )
    return redemption


@transaction.atomic
def transfer_out(
    *,
    account_id,
    other_account_id,
    points: int,
    reason: str = "",
) -> EcosystemPointsEvent:
    if points <= 0:
        raise ValueError("points_must_be_positive")
    source = EcosystemAccount.objects.select_for_update().get(pk=account_id)
    target = EcosystemAccount.objects.select_for_update().get(pk=other_account_id)
    if source.balance_points < points:
        raise ValueError("insufficient_points")
    source.balance_points = source.balance_points - points
    source.save(update_fields=["balance_points"])
    target.balance_points = target.balance_points + points
    target.save(update_fields=["balance_points"])
    out_event = EcosystemPointsEvent.objects.create(
        account=source,
        kind=EcosystemPointsEvent.Kind.TRANSFER_OUT,
        points=-points,
        reference_kind="transfer",
        reason=reason,
    )
    EcosystemPointsEvent.objects.create(
        account=target,
        kind=EcosystemPointsEvent.Kind.TRANSFER_IN,
        points=points,
        reference_kind="transfer",
        reason=reason,
    )
    return out_event


@transaction.atomic
def expire(*, account_id, points: int, reason: str = "scheduled") -> EcosystemPointsEvent:
    if points <= 0:
        raise ValueError("points_must_be_positive")
    account = EcosystemAccount.objects.select_for_update().get(pk=account_id)
    to_expire = min(points, account.balance_points)
    account.balance_points = account.balance_points - to_expire
    account.save(update_fields=["balance_points"])
    return EcosystemPointsEvent.objects.create(
        account=account,
        kind=EcosystemPointsEvent.Kind.EXPIRE,
        points=-to_expire,
        reason=reason,
    )


@transaction.atomic
def manual_adjust(*, account_id, points: int, reason: str) -> EcosystemPointsEvent:
    account = EcosystemAccount.objects.select_for_update().get(pk=account_id)
    account.balance_points = account.balance_points + points
    if points > 0:
        account.lifetime_points = account.lifetime_points + points
    account.save(update_fields=["balance_points", "lifetime_points"])
    event = EcosystemPointsEvent.objects.create(
        account=account,
        kind=EcosystemPointsEvent.Kind.ADJUST,
        points=points,
        reason=reason,
    )
    _recompute_tier(account)
    return event
