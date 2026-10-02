import pytest
from rest_framework.test import APIClient

from products.cymart.partners.models import Partner
from products.cymart.partners.prepare import KitchenInstructions

GF = {"code": "gluten_free", "block_ingredients": ["wheat bread", "wheat"]}

SANDWICH = {
    "item_id": "club-sandwich",
    "calories": 600,
    "carbs_g": 45,
    "ingredients": ["wheat bread", "chicken", "tomato", "onion", "lettuce"],
    "diet_tags": [],
    "modifications": [
        {"ingredient": "tomato", "action": "remove"},
        {"ingredient": "onion", "action": "remove"},
        {"ingredient": "wheat bread", "action": "substitute", "makes": ["gluten_free"],
         "options": [
             {"name": "gluten-free bread", "ingredients": ["rice flour"]},
             {"name": "lettuce wrap"},
         ]},
    ],
}


def _types(res):
    return [(i["type"], i.get("ingredient"), i.get("replacement")) for i in res.instructions]


class TestKitchenInstructions:
    def test_the_brief_example_gluten_free_bread_no_tomato_no_onion(self):
        profile = {"allergies": ["tomato", "onion"], "regimes": [GF]}
        res = KitchenInstructions().prepare(profile, SANDWICH)
        assert res.status == "ok_with_changes"
        kinds = _types(res)
        assert ("remove", "tomato", None) in kinds
        assert ("remove", "onion", None) in kinds
        assert ("substitute", "wheat bread", "gluten-free bread") in kinds
        assert res.instructions[0]["type"] == "allergy_alert"
        assert res.verdict["severity"] == "allow"
        assert "tomato" not in res.modified_item["ingredients"]
        assert "gluten-free bread" in res.modified_item["ingredients"]
        note = res.vendor_note
        assert "NO TOMATO" in note and "NO ONION" in note and "USE GLUTEN-FREE BREAD" in note and "ALLERGY" in note

    def test_no_plan_means_no_changes(self):
        res = KitchenInstructions().prepare({}, SANDWICH)
        assert res.status == "ok" and res.instructions == []

    def test_allergy_alert_present_even_if_nothing_to_change(self):
        item = {"item_id": "x", "calories": 100, "ingredients": ["rice"], "diet_tags": []}
        res = KitchenInstructions().prepare({"allergies": ["peanut"]}, item)
        assert res.status == "ok"
        assert [i["type"] for i in res.instructions] == ["allergy_alert"]

    def test_allergen_without_a_modification_cannot_be_made_safe(self):
        item = {"item_id": "satay", "calories": 300, "ingredients": ["chicken", "peanut sauce"], "modifications": []}
        res = KitchenInstructions().prepare({"allergies": ["peanut"]}, item)
        assert res.status == "cannot_make_safe"
        assert res.verdict["severity"] == "hard_block"
        assert res.unresolved[0]["ingredient"] == "peanut sauce"
        assert "CANNOT MAKE" in res.vendor_note

    def test_substitution_option_containing_the_allergen_is_skipped(self):
        item = {
            "item_id": "bowl", "calories": 400, "ingredients": ["noodles", "chicken"], "diet_tags": [],
            "modifications": [{"ingredient": "noodles", "action": "substitute", "options": [
                {"name": "peanut noodles"}, {"name": "rice noodles"}]}],
        }
        profile = {"allergies": ["wheat"], "regimes": []}
        item["ingredients"] = ["wheat noodles", "chicken"]
        item["modifications"][0]["ingredient"] = "wheat noodles"
        item["modifications"][0]["options"] = [{"name": "whole wheat pasta"}, {"name": "rice noodles"}]
        res = KitchenInstructions().prepare(profile, item)
        assert ("substitute", "wheat noodles", "rice noodles") in _types(res)

    def test_option_ingredient_list_is_checked_for_allergens(self):
        item = {
            "item_id": "bowl", "calories": 400, "ingredients": ["sauce", "chicken"], "diet_tags": [],
            "modifications": [{"ingredient": "sauce", "action": "substitute", "options": [
                {"name": "house sauce", "ingredients": ["sesame", "soy"]},
                {"name": "plain sauce", "ingredients": ["tomato"]}]}],
        }
        # "sauce" itself isn't an allergen here, so nothing is applied
        res = KitchenInstructions().prepare({"allergies": ["sesame"]}, item)
        assert res.status == "ok"
        # but when the original is the problem, the sesame option is rejected
        item["ingredients"] = ["sesame sauce", "chicken"]
        item["modifications"][0]["ingredient"] = "sesame sauce"
        res = KitchenInstructions().prepare({"allergies": ["sesame"]}, item)
        assert ("substitute", "sesame sauce", "plain sauce") in _types(res)

    def test_unknown_ingredients_with_allergy_needs_vendor_confirmation(self):
        item = {"item_id": "mystery", "calories": 500}
        res = KitchenInstructions().prepare({"allergies": ["peanut"]}, item)
        assert res.status == "needs_vendor_confirmation"
        assert any(i["type"] == "verify_ingredients" for i in res.instructions)

    def test_optional_modification_used_to_meet_carb_limit(self):
        burger = {
            "item_id": "burger", "calories": 800, "carbs_g": 48, "diet_tags": ["keto"],
            "ingredients": ["beef", "wheat bun", "cheese"],
            "modifications": [{"ingredient": "wheat bun", "action": "remove", "carbs_g_delta": -35, "calories_delta": -150}],
        }
        profile = {"regimes": [{"code": "keto", "max_item_carbs_g": 15}], "remaining_calories": 900}
        res = KitchenInstructions().prepare(profile, burger)
        assert res.status == "ok_with_changes"
        assert res.modified_item["carbs_g"] == 13 and res.modified_item["calories"] == 650
        assert res.verdict["severity"] == "allow"

    def test_only_modifications_that_help_are_applied(self):
        burger = {
            "item_id": "burger", "calories": 500, "carbs_g": 5, "diet_tags": ["keto"],
            "ingredients": ["beef", "pickle"],
            "modifications": [{"ingredient": "pickle", "action": "remove"}],
        }
        res = KitchenInstructions().prepare({"regimes": [{"code": "keto", "max_item_carbs_g": 15}]}, burger)
        assert res.status == "ok" and res.instructions == []

    def test_modification_matching_is_case_insensitive(self):
        item = {"item_id": "x", "calories": 100, "ingredients": ["Tomato", "Bun"], "diet_tags": [],
                "modifications": [{"ingredient": "tomato", "action": "remove"}]}
        res = KitchenInstructions().prepare({"allergies": ["tomato"]}, item)
        assert res.status == "ok_with_changes"

    def test_still_failing_after_modifications_is_cannot_make_safe(self):
        item = {"item_id": "x", "calories": 900, "carbs_g": 60, "diet_tags": [], "ingredients": ["pasta"],
                "modifications": [{"ingredient": "pasta", "action": "remove", "carbs_g_delta": -5}]}
        profile = {"regimes": [{"code": "keto", "max_item_carbs_g": 15}], "strictness": "strict"}
        res = KitchenInstructions().prepare(profile, item)
        assert res.status == "cannot_make_safe"


@pytest.mark.django_db
class TestPrepareAPI:
    def _client(self):
        _, raw = Partner.create_with_key("Kitchen Platform")
        c = APIClient()
        c.credentials(HTTP_X_API_KEY=raw)
        return c

    def test_requires_api_key(self):
        resp = APIClient().post("/api/v1/partner/prepare/", {"profile": {}, "items": [SANDWICH]}, format="json")
        assert resp.status_code == 403

    def test_end_to_end(self):
        resp = self._client().post(
            "/api/v1/partner/prepare/",
            {"profile": {"allergies": ["tomato", "onion"], "regimes": [GF]}, "items": [SANDWICH]},
            format="json",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["needs_customer_confirmation"] is True
        assert data["can_prepare_all"] is True
        assert data["items"][0]["status"] == "ok_with_changes"
        assert "NO TOMATO" in data["vendor_note"]

    def test_can_prepare_all_false_when_one_item_unfixable(self):
        unfixable = {"item_id": "satay", "calories": 300, "ingredients": ["peanut sauce"]}
        resp = self._client().post(
            "/api/v1/partner/prepare/",
            {"profile": {"allergies": ["peanut"]}, "items": [SANDWICH, unfixable]}, format="json",
        )
        data = resp.json()
        assert data["can_prepare_all"] is False
        assert [i["status"] for i in data["items"]] == ["ok", "cannot_make_safe"]

    def test_validation(self):
        c = self._client()
        assert c.post("/api/v1/partner/prepare/", {"profile": {}, "items": []}, format="json").status_code == 400
        bad = {"item_id": "x", "modifications": [{"ingredient": "a", "action": "substitute"}]}
        assert c.post("/api/v1/partner/prepare/", {"profile": {}, "items": [bad]}, format="json").status_code == 400
        many = [{"item_id": str(n)} for n in range(51)]
        assert c.post("/api/v1/partner/prepare/", {"profile": {}, "items": many}, format="json").status_code == 400
