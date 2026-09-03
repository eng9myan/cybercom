"""Business logic for CyMed Pharmacy Loyalty & Rewards."""
from __future__ import annotations

import uuid
from typing import Any, Optional

from django.db import transaction
from django.utils import timezone


def _recompute_tier(account: Any) -> None:
    from .models import LoyaltyTier

    tier = (
        LoyaltyTier.objects.filter(
            program_id=account.program_id,
            threshold_points__lte=account.lifetime_points,
        )
        .order_by("-threshold_points", "-priority")
        .first()
    )
    if tier is not None and account.current_tier_id != tier.id:
        account.current_tier = tier
        account.save(update_fields=["current_tier", "updated_at"] if _has_updated_at(account) else ["current_tier"])
    elif tier is None and account.current_tier_id is not None:
        account.current_tier = None
        account.save(update_fields=["current_tier", "updated_at"] if _has_updated_at(account) else ["current_tier"])


def _has_updated_at(instance: Any) -> bool:
    return any(f.name == "updated_at" for f in instance._meta.fields)


@transaction.atomic
def enroll(
    *,
    tenant_id: str | uuid.UUID,
    program_id: str | uuid.UUID,
    patient_profile_id: str | uuid.UUID,
) -> Any:
    from .models import PatientLoyaltyAccount

    account, _created = PatientLoyaltyAccount.objects.get_or_create(
        program_id=program_id,
        patient_profile_id=patient_profile_id,
        defaults={
            "tenant_id": tenant_id,
            "balance_points": 0,
            "lifetime_points": 0,
            "joined_at": timezone.now(),
        },
    )
    _recompute_tier(account)
    return account


@transaction.atomic
def earn_points(
    *,
    account_id: str | uuid.UUID,
    points: int,
    reason: str = "",
    reference_order_id: Optional[str | uuid.UUID] = None,
    expires_at: Any = None,
) -> Any:
    from .models import PatientLoyaltyAccount, PointsTransaction

    if points <= 0:
        raise ValueError("points must be positive")

    account = PatientLoyaltyAccount.objects.select_for_update().get(pk=account_id)
    account.balance_points = int(account.balance_points) + points
    account.lifetime_points = int(account.lifetime_points) + points
    account.save(update_fields=["balance_points", "lifetime_points"] + (["updated_at"] if _has_updated_at(account) else []))

    txn = PointsTransaction.objects.create(
        account=account,
        kind=PointsTransaction.Kind.EARN,
        points=points,
        reason=reason,
        reference_order_id=reference_order_id,
        expires_at=expires_at,
    )
    _recompute_tier(account)
    return txn


@transaction.atomic
def redeem_reward(
    *,
    account_id: str | uuid.UUID,
    reward_id: str | uuid.UUID,
    code: str = "",
) -> Any:
    from .models import PatientLoyaltyAccount, PointsTransaction, Redemption, Reward

    account = PatientLoyaltyAccount.objects.select_for_update().get(pk=account_id)
    reward = Reward.objects.select_for_update().get(pk=reward_id)

    if not reward.active:
        raise ValueError("reward is not active")
    if reward.program_id != account.program_id:
        raise ValueError("reward does not belong to account program")
    if account.balance_points < reward.cost_points:
        raise ValueError("insufficient balance points")
    program = account.program
    if reward.cost_points < int(program.min_redemption_points):
        raise ValueError("reward below program minimum redemption threshold")
    if reward.stock_left == 0:
        raise ValueError("reward out of stock")

    if reward.stock_left > 0:
        reward.stock_left = int(reward.stock_left) - 1
        reward.save(update_fields=["stock_left"] + (["updated_at"] if _has_updated_at(reward) else []))

    account.balance_points = int(account.balance_points) - int(reward.cost_points)
    account.save(update_fields=["balance_points"] + (["updated_at"] if _has_updated_at(account) else []))

    PointsTransaction.objects.create(
        account=account,
        kind=PointsTransaction.Kind.REDEEM,
        points=-int(reward.cost_points),
        reason=f"redeem:{reward.code}",
    )

    final_code = code or uuid.uuid4().hex[:16].upper()
    redemption = Redemption.objects.create(
        account=account,
        reward=reward,
        points_spent=int(reward.cost_points),
        code=final_code,
        status=Redemption.Status.ISSUED,
    )
    return redemption


@transaction.atomic
def manual_adjust(
    *,
    account_id: str | uuid.UUID,
    points: int,
    direction: str = "up",
    reason: str = "",
) -> Any:
    from .models import PatientLoyaltyAccount, PointsTransaction

    if points <= 0:
        raise ValueError("points must be positive")

    account = PatientLoyaltyAccount.objects.select_for_update().get(pk=account_id)

    if direction == "up":
        kind = PointsTransaction.Kind.ADJUST_UP
        account.balance_points = int(account.balance_points) + points
        account.lifetime_points = int(account.lifetime_points) + points
        signed = points
    elif direction == "down":
        kind = PointsTransaction.Kind.ADJUST_DOWN
        account.balance_points = int(account.balance_points) - points
        signed = -points
    else:
        raise ValueError("direction must be 'up' or 'down'")

    update_fields = ["balance_points", "lifetime_points"] if direction == "up" else ["balance_points"]
    if _has_updated_at(account):
        update_fields.append("updated_at")
    account.save(update_fields=update_fields)

    txn = PointsTransaction.objects.create(
        account=account,
        kind=kind,
        points=signed,
        reason=reason,
    )
    _recompute_tier(account)
    return txn


@transaction.atomic
def expire_points(
    *,
    account_id: str | uuid.UUID,
    points: int,
    reason: str = "",
) -> Any:
    from .models import PatientLoyaltyAccount, PointsTransaction

    if points <= 0:
        raise ValueError("points must be positive")

    account = PatientLoyaltyAccount.objects.select_for_update().get(pk=account_id)
    account.balance_points = max(0, int(account.balance_points) - points)
    account.save(update_fields=["balance_points"] + (["updated_at"] if _has_updated_at(account) else []))

    txn = PointsTransaction.objects.create(
        account=account,
        kind=PointsTransaction.Kind.EXPIRE,
        points=-points,
        reason=reason or "points expired",
    )
    return txn
