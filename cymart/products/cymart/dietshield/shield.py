"""The Diet Shield — a three-gate policy check on cart items.

Gates run in order and the verdict is the strictest of the three:

    1. Safety   — allergies / medical. Allergy hit = HARD_BLOCK (never
                  overridable, whatever the strictness mode).
    2. Regime   — composition rules (keto, gluten-free, vegan, halal…).
    3. Quantity — calories vs the day's remaining budget.

No DietProfile → the caller skips this entirely and the cart passes
through unguarded. This mirrors the catalog's existing policy gates
(restricted / prescription / age).
"""

from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field
from decimal import Decimal

from .models import DietDay, DietPlan, DietProfile, NutritionFact, Strictness
from .nutrition import NutritionResolver


class Severity(enum.IntEnum):
    ALLOW = 0
    WARN = 1
    BLOCK = 2
    HARD_BLOCK = 3


@dataclass
class LineVerdict:
    product_id: uuid.UUID
    severity: Severity
    gate: str = ""
    reason: str = ""
    # Populated by a later catalog-search phase; None for now.
    swap_suggestion: uuid.UUID | None = None

    @property
    def allowed(self) -> bool:
        return self.severity <= Severity.WARN


@dataclass
class ShieldResult:
    overall: Severity
    lines: list[LineVerdict] = field(default_factory=list)
    remaining_calories_before: Decimal = Decimal("0")
    projected_calories_after: Decimal = Decimal("0")

    @property
    def allowed(self) -> bool:
        return self.overall <= Severity.WARN


def _tokens(values) -> set[str]:
    return {str(v).strip().lower() for v in (values or []) if str(v).strip()}


class DietShield:
    def __init__(self, resolver: NutritionResolver | None = None):
        self._resolver = resolver or NutritionResolver()

    def _soft_severity(self, strictness: str, is_hard: bool = True) -> Severity:
        """A violation is a BLOCK only under STRICT (and only for hard
        rules); balanced and coach downgrade to WARN."""
        if strictness == Strictness.STRICT and is_hard:
            return Severity.BLOCK
        return Severity.WARN

    def _gate_safety(
        self, profile: DietProfile, fact: NutritionFact, strictness: str
    ) -> LineVerdict | None:
        allergies = _tokens(profile.allergies)
        if allergies:
            present = _tokens(fact.contains_allergens) | _tokens(fact.ingredients)
            hit = allergies & present
            if hit:
                return LineVerdict(
                    fact.product_id,
                    Severity.HARD_BLOCK,
                    "safety",
                    f"Contains allergen(s): {', '.join(sorted(hit))}.",
                )
        conditions = _tokens(profile.medical_conditions)
        if "hypertension" in conditions and float(fact.sodium_mg) > 1000:
            return LineVerdict(
                fact.product_id,
                self._soft_severity(strictness),
                "safety",
                f"High sodium ({int(fact.sodium_mg)}mg) for hypertension.",
            )
        if "diabetes" in conditions and float(fact.sugar_g) > 25:
            return LineVerdict(
                fact.product_id,
                self._soft_severity(strictness),
                "safety",
                f"High sugar ({int(fact.sugar_g)}g) for diabetes.",
            )
        return None

    def _gate_regime(
        self, profile: DietProfile, fact: NutritionFact, strictness: str
    ) -> LineVerdict | None:
        item_tags = _tokens(fact.diet_tags)
        item_ings = _tokens(fact.ingredients)
        for regime in profile.regimes.all():
            if not regime.is_active:
                continue
            blocked = _tokens(regime.block_ingredients) & item_ings
            if blocked:
                return LineVerdict(
                    fact.product_id,
                    self._soft_severity(strictness, regime.is_hard),
                    "regime",
                    f"{regime.name_en}: contains {', '.join(sorted(blocked))}.",
                )
            if (
                regime.max_item_carbs_g is not None
                and fact.carbs_g > regime.max_item_carbs_g
            ):
                return LineVerdict(
                    fact.product_id,
                    self._soft_severity(strictness, regime.is_hard),
                    "regime",
                    f"{regime.name_en}: {int(fact.carbs_g)}g carbs over "
                    f"{int(regime.max_item_carbs_g)}g limit.",
                )
            if regime.code not in item_tags:
                return LineVerdict(
                    fact.product_id,
                    self._soft_severity(strictness, regime.is_hard),
                    "regime",
                    f"Not marked {regime.name_en}-compatible.",
                )
        return None

    def _gate_quantity(
        self,
        fact: NutritionFact,
        quantity: Decimal,
        remaining: Decimal,
        strictness: str,
    ) -> LineVerdict | None:
        item_cal = fact.calories * quantity
        if item_cal > remaining:
            over = int(item_cal - remaining)
            return LineVerdict(
                fact.product_id,
                self._soft_severity(strictness),
                "quantity",
                f"{int(item_cal)} kcal exceeds remaining budget by {over} kcal.",
            )
        return None

    def evaluate(
        self,
        profile: DietProfile,
        plan: DietPlan,
        day: DietDay | None,
        items: list[dict],
    ) -> ShieldResult:
        """items: [{"product_id": UUID, "quantity": Decimal}, ...]"""
        strictness = profile.strictness
        consumed = Decimal(day.consumed_calories) if day else Decimal("0")
        remaining = Decimal(plan.daily_calories) - consumed
        remaining_start = remaining

        product_ids = [i["product_id"] for i in items]
        facts = self._resolver.resolve_many(product_ids)

        lines: list[LineVerdict] = []
        for item in items:
            pid = item["product_id"]
            qty = Decimal(str(item.get("quantity", 1)))
            fact = facts.get(pid)

            if fact is None:
                # Unknown nutrition: can't verify. Guard when the profile
                # has anything to enforce; otherwise let it pass with a note.
                has_rules = bool(profile.allergies) or profile.regimes.exists()
                sev = (
                    Severity.BLOCK
                    if (has_rules and strictness == Strictness.STRICT)
                    else Severity.WARN
                )
                lines.append(
                    LineVerdict(pid, sev, "unknown", "No nutrition data for item.")
                )
                continue

            verdict = (
                self._gate_safety(profile, fact, strictness)
                or self._gate_regime(profile, fact, strictness)
                or self._gate_quantity(fact, qty, remaining, strictness)
            )
            if verdict is None:
                verdict = LineVerdict(pid, Severity.ALLOW, "ok", "Fits your plan.")
                remaining -= fact.calories * qty
            lines.append(verdict)

        overall = max((ln.severity for ln in lines), default=Severity.ALLOW)
        return ShieldResult(
            overall=overall,
            lines=lines,
            remaining_calories_before=remaining_start,
            projected_calories_after=remaining,
        )
