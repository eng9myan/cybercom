"""Application services for the Diet Shield: profile upsert + plan build,
daily consumption tracking, and the cart-facing gate.

The gate (``ShieldGate``) is the single entry point other apps use — it
loads the profile/plan/day and runs the pure ``DietShield`` evaluator.
When a customer has no ``DietProfile`` it returns ``None`` so callers
(e.g. the cart) pass through unguarded.
"""

from __future__ import annotations

import datetime
import uuid
from decimal import Decimal

from django.db import transaction

from .models import DietDay, DietPlan, DietProfile, DietRegime
from .plan_builder import PlanBuilder
from .shield import DietShield, Severity, ShieldResult


class DietShieldBlockedError(Exception):
    """Raised when the shield blocks a cart action. Carries the result so
    the caller can surface the reason and swap suggestion."""

    def __init__(self, result: ShieldResult):
        self.result = result
        blocked = [ln for ln in result.lines if ln.severity >= Severity.BLOCK]
        reason = blocked[0].reason if blocked else "Blocked by your diet plan."
        super().__init__(reason)


class ProfileService:
    def upsert(
        self,
        customer_id: uuid.UUID,
        data: dict,
        regime_codes: list[str] | None = None,
        rebuild_plan: bool = True,
    ) -> tuple[DietProfile, DietPlan | None]:
        with transaction.atomic():
            profile, _ = DietProfile.objects.update_or_create(
                customer_id=customer_id, defaults=data
            )
            if regime_codes is not None:
                regimes = DietRegime.objects.filter(code__in=regime_codes, is_active=True)
                profile.regimes.set(regimes)
            plan = PlanBuilder().build(profile) if rebuild_plan else None
        return profile, plan

    def get(self, customer_id: uuid.UUID) -> DietProfile | None:
        return DietProfile.objects.filter(customer_id=customer_id).first()

    def active_plan(self, profile: DietProfile) -> DietPlan | None:
        return profile.plans.filter(is_active=True).first()


class DietDayService:
    def today(self) -> datetime.date:
        return datetime.date.today()

    def get_or_create_today(self, profile: DietProfile) -> DietDay:
        day, _ = DietDay.objects.get_or_create(profile=profile, date=self.today())
        return day

    def get_today(self, profile: DietProfile) -> DietDay | None:
        return DietDay.objects.filter(profile=profile, date=self.today()).first()

    def log(
        self,
        profile: DietProfile,
        calories: Decimal,
        protein_g: Decimal = Decimal("0"),
        carbs_g: Decimal = Decimal("0"),
        fat_g: Decimal = Decimal("0"),
        off_plan: bool = False,
    ) -> DietDay:
        with transaction.atomic():
            day = DietDay.objects.select_for_update().get_or_create(
                profile=profile, date=self.today()
            )[0]
            day.consumed_calories += Decimal(calories)
            day.consumed_protein_g += Decimal(protein_g)
            day.consumed_carbs_g += Decimal(carbs_g)
            day.consumed_fat_g += Decimal(fat_g)
            if off_plan:
                day.off_plan_overrides += 1
            day.save()
        return day

    def status(self, profile: DietProfile, plan: DietPlan) -> dict:
        day = self.get_today(profile)
        consumed = Decimal(day.consumed_calories) if day else Decimal("0")
        remaining = Decimal(plan.daily_calories) - consumed
        return {
            "date": self.today().isoformat(),
            "daily_calories": plan.daily_calories,
            "consumed_calories": int(consumed),
            "remaining_calories": int(remaining),
            "on_track": remaining >= 0,
            "protein_g_target": plan.protein_g,
            "protein_g_consumed": int(day.consumed_protein_g) if day else 0,
            "off_plan_overrides": day.off_plan_overrides if day else 0,
        }


class ShieldGate:
    """The bridge other apps call. Read-only; never mutates the cart."""

    def __init__(self):
        self._profiles = ProfileService()
        self._days = DietDayService()
        self._shield = DietShield()

    def evaluate_items(
        self, customer_id: uuid.UUID, items: list[dict]
    ) -> ShieldResult | None:
        profile = self._profiles.get(customer_id)
        if profile is None or not profile.is_active:
            return None
        plan = self._profiles.active_plan(profile) or PlanBuilder().build(profile)
        day = self._days.get_today(profile)
        return self._shield.evaluate(profile, plan, day, items)

    def enforce(self, customer_id: uuid.UUID, items: list[dict]) -> ShieldResult | None:
        """Evaluate and raise DietShieldBlockedError if the cart would be
        blocked (BLOCK / HARD_BLOCK). WARN and below pass through."""
        result = self.evaluate_items(customer_id, items)
        if result is not None and result.overall >= Severity.BLOCK:
            raise DietShieldBlockedError(result)
        return result
