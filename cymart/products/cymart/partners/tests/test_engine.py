import pytest

from products.cymart.partners.engine import PartnerShieldEngine


@pytest.mark.django_db
class TestPartnerShieldEngine:
    def test_allows_item_with_no_rules(self):
        result = PartnerShieldEngine().evaluate({}, [{"item_id": "1", "calories": 400}])
        assert result.overall == "allow"
        assert result.allowed is True

    def test_allergy_is_hard_block_regardless_of_strictness(self):
        profile = {"allergies": ["peanut"], "strictness": "coach"}
        items = [{"item_id": "1", "ingredients": ["chicken", "peanut"]}]
        result = PartnerShieldEngine().evaluate(profile, items)
        assert result.overall == "hard_block"
        assert result.allowed is False

    def test_allergy_matching_is_substring_aware(self):
        # Real-world ingredient listings aren't single controlled-vocab
        # tokens — "peanut sauce" must still trip an allergy on "peanut".
        profile = {"allergies": ["peanut"]}
        items = [{"item_id": "1", "ingredients": ["chicken", "peanut sauce"]}]
        result = PartnerShieldEngine().evaluate(profile, items)
        assert result.overall == "hard_block"

    def test_regime_ingredient_block_strict_mode(self):
        profile = {
            "strictness": "strict",
            "regimes": [{"code": "keto", "block_ingredients": ["wheat", "sugar"]}],
        }
        items = [{"item_id": "1", "ingredients": ["wheat", "cream"], "diet_tags": []}]
        result = PartnerShieldEngine().evaluate(profile, items)
        assert result.overall == "block"

    def test_regime_ingredient_block_balanced_mode_is_warn(self):
        profile = {
            "strictness": "balanced",
            "regimes": [{"code": "keto", "block_ingredients": ["wheat"]}],
        }
        items = [{"item_id": "1", "ingredients": ["wheat"], "diet_tags": []}]
        result = PartnerShieldEngine().evaluate(profile, items)
        assert result.overall == "warn"
        assert result.allowed is True  # warn still allowed

    def test_max_carbs_regime_rule(self):
        profile = {
            "strictness": "strict",
            "regimes": [{"code": "keto", "max_item_carbs_g": 15}],
        }
        items = [{"item_id": "1", "carbs_g": 80, "diet_tags": ["keto"]}]
        result = PartnerShieldEngine().evaluate(profile, items)
        assert result.overall == "block"
        assert "carbs" in result.lines[0].reason

    def test_quantity_gate_against_remaining_calories(self):
        profile = {"remaining_calories": 300, "strictness": "strict"}
        items = [{"item_id": "1", "calories": 500}]
        result = PartnerShieldEngine().evaluate(profile, items)
        assert result.overall == "block"

    def test_item_fitting_everything_is_allowed(self):
        profile = {
            "allergies": ["peanut"],
            "regimes": [{"code": "keto", "max_item_carbs_g": 15}],
            "remaining_calories": 600,
            "strictness": "strict",
        }
        items = [
            {
                "item_id": "safe-1", "calories": 480, "carbs_g": 6,
                "ingredients": ["chicken", "olive oil"], "diet_tags": ["keto"],
            }
        ]
        result = PartnerShieldEngine().evaluate(profile, items)
        assert result.overall == "allow"
        assert result.lines[0].item_id == "safe-1"

    def test_verdicts_carry_stable_machine_readable_codes(self):
        profile = {
            "allergies": ["peanut"],
            "regimes": [{"code": "keto", "max_item_carbs_g": 15, "block_ingredients": ["sugar"]}],
            "remaining_calories": 300,
            "strictness": "strict",
        }
        items = [
            {"item_id": "a", "ingredients": ["peanut"]},
            {"item_id": "b", "ingredients": ["sugar"], "diet_tags": ["keto"]},
            {"item_id": "c", "ingredients": ["beef"], "carbs_g": 50, "diet_tags": ["keto"]},
            {"item_id": "d", "ingredients": ["beef"], "carbs_g": 5, "diet_tags": []},
            {"item_id": "e", "ingredients": ["beef"], "carbs_g": 5, "diet_tags": ["keto"], "calories": 900},
            {"item_id": "f", "ingredients": ["beef"], "carbs_g": 5, "diet_tags": ["keto"], "calories": 100},
            {"item_id": "g", "carbs_g": 5, "diet_tags": ["keto"], "calories": 100},
        ]
        codes = {ln.item_id: ln.code for ln in PartnerShieldEngine().evaluate(profile, items).lines}
        assert codes == {
            "a": "allergen_conflict",
            "b": "regime_blocked_ingredient",
            "c": "regime_carb_limit",
            "d": "regime_not_compatible",
            "e": "calorie_budget_exceeded",
            "f": "ok",
            "g": "ingredients_unknown",
        }

    def test_missing_ingredients_is_never_reported_as_safe_when_user_has_allergies(self):
        profile = {"allergies": ["peanut"], "strictness": "strict"}
        line = PartnerShieldEngine().evaluate(profile, [{"item_id": "x", "calories": 300}]).lines[0]
        assert line.code == "ingredients_unknown"
        assert line.severity == "block"  # strict mode: can't verify -> don't let it through

        balanced = PartnerShieldEngine().evaluate(
            {"allergies": ["peanut"], "strictness": "balanced"}, [{"item_id": "x"}]
        ).lines[0]
        assert balanced.severity == "warn"

    def test_missing_ingredients_is_fine_when_user_has_no_allergies(self):
        line = PartnerShieldEngine().evaluate({}, [{"item_id": "x", "calories": 300}]).lines[0]
        assert line.severity == "allow"

    def test_matched_lists_the_offending_allergen(self):
        profile = {"allergies": ["peanut", "shellfish"]}
        items = [{"item_id": "1", "ingredients": ["chicken", "peanut sauce"]}]
        line = PartnerShieldEngine().evaluate(profile, items).lines[0]
        assert line.matched == ["peanut"]

    def test_swap_is_first_alternative_that_passes_every_gate(self):
        profile = {
            "allergies": ["peanut"],
            "regimes": [{"code": "keto", "max_item_carbs_g": 15}],
            "strictness": "strict",
        }
        items = [
            {
                "item_id": "pasta",
                "carbs_g": 82,
                "diet_tags": [],
                "ingredients": ["wheat", "cream"],
                "alternatives": [
                    {"item_id": "satay", "carbs_g": 5, "diet_tags": ["keto"], "ingredients": ["peanut"]},
                    {"item_id": "high-carb-bowl", "carbs_g": 60, "diet_tags": ["keto"], "ingredients": ["rice"]},
                    {"item_id": "no-data-bowl", "carbs_g": 5, "diet_tags": ["keto"]},
                    {"item_id": "chicken-bowl", "carbs_g": 6, "diet_tags": ["keto"], "ingredients": ["chicken"]},
                    {"item_id": "also-fine", "carbs_g": 4, "diet_tags": ["keto"], "ingredients": ["beef"]},
                ],
            }
        ]
        line = PartnerShieldEngine().evaluate(profile, items).lines[0]
        assert line.severity == "block"
        assert line.swap == {"item_id": "chicken-bowl"}

    def test_no_swap_when_item_is_allowed_or_nothing_qualifies(self):
        profile = {"allergies": ["peanut"]}
        ok_item = {"item_id": "ok", "ingredients": ["chicken"], "alternatives": [{"item_id": "x"}]}
        bad_item = {
            "item_id": "bad", "ingredients": ["peanut"],
            "alternatives": [{"item_id": "also-bad", "ingredients": ["peanut"]}],
        }
        lines = PartnerShieldEngine().evaluate(profile, [ok_item, bad_item]).lines
        assert lines[0].swap is None
        assert lines[1].swap is None

    def test_independent_mode_checks_each_item_against_full_budget(self):
        profile = {"remaining_calories": 700, "strictness": "balanced"}
        items = [{"item_id": "a", "calories": 480}, {"item_id": "b", "calories": 320}]
        lines = PartnerShieldEngine().evaluate(profile, items).lines
        assert [ln.severity for ln in lines] == ["allow", "allow"]

    def test_cumulative_mode_treats_items_as_a_cart_with_a_shrinking_budget(self):
        profile = {"remaining_calories": 700, "strictness": "balanced"}
        items = [{"item_id": "a", "calories": 480}, {"item_id": "b", "calories": 320}]
        lines = PartnerShieldEngine().evaluate(profile, items, cumulative=True).lines
        assert [ln.severity for ln in lines] == ["allow", "warn"]
        assert lines[1].code == "calorie_budget_exceeded"

    def test_multiple_items_overall_is_the_strictest(self):
        profile = {"allergies": ["peanut"]}
        items = [
            {"item_id": "ok", "ingredients": ["chicken"]},
            {"item_id": "bad", "ingredients": ["peanut"]},
        ]
        result = PartnerShieldEngine().evaluate(profile, items)
        assert result.overall == "hard_block"
        assert {ln.item_id: ln.severity for ln in result.lines} == {
            "ok": "allow", "bad": "hard_block",
        }
