"""Resolves per-product nutrition + diet tags for the shield.

Reads the NutritionFact cache. When a product has no fact yet, returns
None and the shield treats it as unknown (strictness decides the verdict).
The AI-estimation fallback (name/category/photo → macros + tags) plugs in
here in a later phase — the shield never has to change.
"""

from __future__ import annotations

import uuid

from .models import NutritionFact


class NutritionResolver:
    def resolve(self, product_id: uuid.UUID) -> NutritionFact | None:
        return NutritionFact.objects.filter(product_id=product_id).first()

    def resolve_many(self, product_ids: list[uuid.UUID]) -> dict[uuid.UUID, NutritionFact]:
        facts = NutritionFact.objects.filter(product_id__in=product_ids)
        return {f.product_id: f for f in facts}
