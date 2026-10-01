import uuid
from decimal import Decimal

import pytest

from products.cymart.dietshield.models import (
    ActivityLevel, DietProfile, DietRegime, GoalType, NutritionFact, Sex,
)
from products.cymart.pantry.services import GroceryListBuilder, RecipeResolver


@pytest.mark.django_db
class TestRecipeResolver:
    def test_resolve_shakshuka_seeded_recipe(self):
        ingredients = RecipeResolver().resolve("shakshuka")
        names = {i["ingredient_name"] for i in ingredients}
        assert "eggs" in names and "tomato" in names

    def test_resolve_scales_by_servings(self):
        base = RecipeResolver().resolve("shakshuka")  # servings=2
        scaled = RecipeResolver().resolve("shakshuka", servings=4)
        eggs_base = next(i for i in base if i["ingredient_name"] == "eggs")["quantity"]
        eggs_scaled = next(i for i in scaled if i["ingredient_name"] == "eggs")["quantity"]
        assert eggs_scaled == eggs_base * 2

    def test_unknown_recipe_returns_empty(self):
        assert RecipeResolver().resolve("not-a-real-recipe") == []

    def test_explode_dedupes_shared_ingredients(self):
        merged = RecipeResolver().explode(["shakshuka", "greek_salad"])
        tomato_entries = [i for i in merged if i["ingredient_name"] == "tomato"]
        assert len(tomato_entries) == 1
        assert tomato_entries[0]["quantity"] == Decimal("6")  # 4 + 2


@pytest.mark.django_db
class TestGroceryListBuilder:
    def test_match_ingredients_finds_by_name(self):
        NutritionFact.objects.create(
            product_id=uuid.uuid4(), name_snapshot="Free-range eggs (6-pack)",
            ingredients=["eggs"],
        )
        result = GroceryListBuilder().match_ingredients(
            [{"ingredient_name": "eggs", "quantity": Decimal("6"), "unit": "pcs"}]
        )
        assert len(result["matched"]) == 1
        assert result["unmatched"] == []

    def test_unmatched_ingredient_surfaces_separately(self):
        result = GroceryListBuilder().match_ingredients(
            [{"ingredient_name": "dragonfruit", "quantity": Decimal("1"), "unit": "pcs"}]
        )
        assert result["matched"] == []
        assert len(result["unmatched"]) == 1

    def test_from_recipes_end_to_end(self):
        NutritionFact.objects.create(
            product_id=uuid.uuid4(), name_snapshot="Cage-free eggs", ingredients=["eggs"]
        )
        NutritionFact.objects.create(
            product_id=uuid.uuid4(), name_snapshot="Roma tomato", ingredients=["tomato"]
        )
        result = GroceryListBuilder().from_recipes(["shakshuka"])
        matched_names = {m["ingredient_name"] for m in result["matched"]}
        assert "eggs" in matched_names and "tomato" in matched_names
        # Structural invariant, robust to whatever else the seeded catalog
        # (25 restaurants + 3 hypermarkets) happens to also match: every
        # shakshuka ingredient lands in exactly one of matched/unmatched.
        shakshuka_ingredient_count = len(RecipeResolver().resolve("shakshuka"))
        assert len(result["matched"]) + len(result["unmatched"]) == shakshuka_ingredient_count

    def test_from_plan_filters_by_regime_tag(self):
        profile = DietProfile.objects.create(
            customer_id=uuid.uuid4(), sex=Sex.MALE, age=35, height_cm=Decimal("175"),
            weight_kg=Decimal("80"), activity_level=ActivityLevel.MODERATE,
            goal_type=GoalType.MAINTAIN,
        )
        keto, _ = DietRegime.objects.get_or_create(
            code="keto", defaults={"name_en": "Keto", "max_item_carbs_g": Decimal("15")}
        )
        profile.regimes.add(keto)
        NutritionFact.objects.create(
            product_id=uuid.uuid4(), name_snapshot="Keto chicken pack",
            diet_tags=["keto"], calories=Decimal("500"),
        )
        NutritionFact.objects.create(
            product_id=uuid.uuid4(), name_snapshot="White bread", diet_tags=[],
        )
        # A large days value so the test's own item isn't crowded out of
        # the (documented MVP, unranked) slice by the seeded catalog's own
        # keto-tagged items.
        basket = GroceryListBuilder().from_plan(profile, days=1000)
        names = {b["product_name"] for b in basket}
        assert "Keto chicken pack" in names
        assert "White bread" not in names
