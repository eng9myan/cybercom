"""Starter diet-rule packs and the starter weekly-grocery template.

These are a STARTING POINT for the platform's nutrition or compliance team to review and extend:
they are not clinical guidance and not a certification (for example, "halal" here only blocks
obviously non-halal ingredients; it does not verify slaughter or certification).

Remember the matching rule: allergies match partially ("peanut" also catches "peanut sauce") and by group ("dairy" catches "cheese", see allergens.py),
but regime ingredients match WHOLE names, so list the variants your catalog uses.
"""

from __future__ import annotations

REGIME_PACKS: dict[str, dict] = {
    "keto": {"block_ingredients": ["sugar", "wheat", "wheat bun", "rice", "potato", "bread", "pasta", "flour", "corn", "oats"]},
    "low_carb": {"block_ingredients": ["sugar"]},
    "halal": {"block_ingredients": ["pork", "bacon", "ham", "lard", "alcohol", "wine", "beer", "gelatin"]},
    "vegan": {"block_ingredients": ["meat", "chicken", "beef", "lamb", "fish", "tuna", "shrimp", "egg", "milk", "cheese",
                                    "butter", "cream", "yogurt", "honey", "gelatin", "mayo", "mozzarella", "feta"]},
    "vegetarian": {"block_ingredients": ["meat", "chicken", "beef", "lamb", "fish", "tuna", "shrimp", "bacon", "ham", "gelatin"]},
    "gluten_free": {"block_ingredients": ["wheat", "wheat bun", "wheat bread", "barley", "rye", "malt", "flour", "bread",
                                          "pasta", "couscous", "bulgur", "semolina", "freekeh"]},
}

# Weekly servings per food group for the grocery basket. A starter template: the platform can send its own `needs`.
DEFAULT_WEEKLY_SERVINGS = {"protein": 14, "vegetables": 21, "fruit": 7, "dairy": 7, "grains": 14, "fats": 7, "snacks": 7}
REGIME_WEEKLY_OVERRIDES = {
    "keto": {"grains": 0, "fruit": 2},
    "low_carb": {"grains": 7},
}

MEAL_SPLIT = {"breakfast": 0.25, "lunch": 0.30, "dinner": 0.30, "snack": 0.15}


def regime_rule(code: str, daily_carbs_g: int | None = None) -> dict:
    """The shield rule for a regime code: the starter pack plus, for keto/low-carb, a per-item carb cap."""
    rule = {"code": code, "block_ingredients": list(REGIME_PACKS.get(code, {}).get("block_ingredients", []))}
    if code == "keto" and daily_carbs_g is not None:
        rule["max_item_carbs_g"] = max(10, round(daily_carbs_g / 2))  # no single item more than half the day's carbs
    elif code == "low_carb":
        rule["max_item_carbs_g"] = 40
    return rule
