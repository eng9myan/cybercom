"""The grocery brain: learn buy rhythm, predict run-out, turn recipes and
diet plans into shopping lists.

Reuses dietshield's NutritionFact cache to resolve ingredient tokens to
real SKUs — same dependency posture as dietshield.NutritionResolver: it
reads whatever nutrition data exists and reports what it couldn't match,
rather than owning the catalog itself.
"""

from __future__ import annotations

import datetime
import uuid
from decimal import Decimal

from django.db import transaction

from .models import PantryItem, PurchaseHistory, PurchaseSource, Recipe

# How close to the predicted run-out date before an item is "due".
DEFAULT_BUFFER_DAYS = 1
# Exponential-moving-average weight given to a freshly observed interval
# vs. the previously learned typical interval.
INTERVAL_SMOOTHING = Decimal("0.3")


class ReplenishEngine:
    def record_purchase(
        self,
        customer_id: uuid.UUID,
        product_id: uuid.UUID,
        quantity: Decimal,
        unit: str = "",
        product_name: str = "",
        purchased_at: datetime.date | None = None,
        source: str = PurchaseSource.ORDER,
    ) -> PantryItem:
        purchased_at = purchased_at or datetime.date.today()

        with transaction.atomic():
            PurchaseHistory.objects.create(
                customer_id=customer_id,
                product_id=product_id,
                product_name_snapshot=product_name,
                quantity=quantity,
                unit=unit,
                purchased_at=purchased_at,
                source=source,
            )

            item, created = PantryItem.objects.select_for_update().get_or_create(
                customer_id=customer_id,
                product_id=product_id,
                defaults={"product_name_snapshot": product_name, "unit": unit},
            )

            if not created and item.last_purchased_at:
                interval = (purchased_at - item.last_purchased_at).days
                if interval > 0:
                    if item.typical_interval_days:
                        blended = (
                            Decimal(item.typical_interval_days) * (1 - INTERVAL_SMOOTHING)
                            + Decimal(interval) * INTERVAL_SMOOTHING
                        )
                        item.typical_interval_days = int(round(blended))
                    else:
                        item.typical_interval_days = interval

            item.last_purchased_at = purchased_at
            item.last_quantity = quantity
            if product_name:
                item.product_name_snapshot = product_name
            if unit:
                item.unit = unit
            if item.typical_interval_days:
                item.predicted_runout_date = purchased_at + datetime.timedelta(
                    days=item.typical_interval_days
                )
            item.save()
        return item

    def due_for_replenish(
        self,
        customer_id: uuid.UUID,
        as_of: datetime.date | None = None,
        buffer_days: int = DEFAULT_BUFFER_DAYS,
    ):
        as_of = as_of or datetime.date.today()
        cutoff = as_of + datetime.timedelta(days=buffer_days)
        return PantryItem.objects.filter(
            customer_id=customer_id,
            is_tracked=True,
            predicted_runout_date__isnull=False,
            predicted_runout_date__lte=cutoff,
        )

    def build_refill_basket(
        self, customer_id: uuid.UUID, as_of: datetime.date | None = None
    ) -> list[dict]:
        """Repeat-buy basket: last quantity of everything predicted low.
        Staged for the customer to confirm — never auto-ordered."""
        return [
            {
                "product_id": i.product_id,
                "product_name": i.product_name_snapshot,
                "quantity": i.last_quantity,
                "unit": i.unit,
                "predicted_runout_date": i.predicted_runout_date,
            }
            for i in self.due_for_replenish(customer_id, as_of=as_of)
        ]


class RecipeResolver:
    def resolve(self, code: str, servings: int | None = None) -> list[dict]:
        recipe = Recipe.objects.filter(code=code, is_active=True).first()
        if recipe is None:
            return []
        scale = Decimal(servings) / Decimal(recipe.servings) if servings else Decimal("1")
        return [
            {
                "ingredient_name": ing.ingredient_name,
                "quantity": ing.quantity * scale,
                "unit": ing.unit,
            }
            for ing in recipe.ingredients.all()
        ]

    def explode(
        self, codes: list[str], servings_map: dict[str, int] | None = None
    ) -> list[dict]:
        """Merge several recipes' ingredients into one deduped list —
        cooking 3 dinners this week shouldn't buy onions 3 times."""
        merged: dict[tuple[str, str], dict] = {}
        for code in codes:
            servings = (servings_map or {}).get(code)
            for ing in self.resolve(code, servings):
                key = (ing["ingredient_name"], ing["unit"])
                if key in merged:
                    merged[key]["quantity"] += ing["quantity"]
                else:
                    merged[key] = dict(ing)
        return list(merged.values())


class GroceryListBuilder:
    def _all_facts(self):
        from products.cymart.dietshield.models import NutritionFact

        return list(NutritionFact.objects.all())

    def match_ingredients(self, ingredients: list[dict]) -> dict:
        """Resolve free-text ingredient tokens to real SKUs via the
        nutrition cache. Returns matched (with product_id) and unmatched
        (for the caller to surface — "couldn't find tahini nearby")."""
        facts = self._all_facts()
        matched, unmatched = [], []
        for ing in ingredients:
            name = ing["ingredient_name"].strip().lower()
            hit = next(
                (
                    f
                    for f in facts
                    if name in (f.name_snapshot or "").lower()
                    or name in {str(x).strip().lower() for x in (f.ingredients or [])}
                ),
                None,
            )
            if hit is not None:
                matched.append(
                    {
                        "ingredient_name": name,
                        "product_id": hit.product_id,
                        "product_name": hit.name_snapshot,
                        "quantity": ing["quantity"],
                        "unit": ing["unit"],
                    }
                )
            else:
                unmatched.append(ing)
        return {"matched": matched, "unmatched": unmatched}

    def from_recipes(
        self, codes: list[str], servings_map: dict[str, int] | None = None
    ) -> dict:
        ingredients = RecipeResolver().explode(codes, servings_map)
        return self.match_ingredients(ingredients)

    def from_plan(self, profile, days: int = 7) -> list[dict]:
        """A week's grocery basket that stays inside the diet plan's
        regimes — items from the nutrition cache tagged with any of the
        profile's regime codes. MVP selection; ranking/pricing/dedup
        against what's already in the pantry comes later."""
        regime_codes = {c.lower() for c in profile.regimes.values_list("code", flat=True)}
        facts = self._all_facts()
        if regime_codes:
            facts = [
                f
                for f in facts
                if regime_codes & {t.lower() for t in (f.diet_tags or [])}
            ]
        return [
            {
                "product_id": f.product_id,
                "product_name": f.name_snapshot,
                "calories": f.calories,
                "protein_g": f.protein_g,
                "carbs_g": f.carbs_g,
            }
            for f in facts[:days]
        ]
