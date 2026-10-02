import re

import pytest
from rest_framework.test import APIClient

from products.cymart.partners.agent.providers.sandbox import SandboxCompletionProvider  # noqa: F401  (default provider)
from products.cymart.partners.models import Partner
from products.cymart.partners.planner.basket import build_basket, weekly_needs
from products.cymart.partners.planner.targets import build_targets
from products.cymart.partners.planner.weekly import plan_week
from products.cymart.partners.tests.test_agent import FakePlatform

ARABIC = re.compile("[؀-ۿ]")


def intake(**kw):
    base = {"sex": "female", "age": 30, "height_cm": 165, "weight_kg": 70, "activity": "sedentary", "goal": "lose",
            "weekly_pace_kg": 0.5, "allergies": ["peanut"], "regimes": []}
    base.update(kw)
    return base


class TestTargets:
    def test_floor_is_applied_when_the_deficit_would_go_below_it(self):
        # BMR 1420, TDEE 1704, minus 550 a day would be 1154: below the 1,200 floor
        r = build_targets(intake())
        assert r["bmr"] == 1420 and r["tdee"] == 1704
        assert r["daily_calories"] == 1200 and r["safety_floor"] == 1200
        assert [w["code"] for w in r["warnings"]] == ["floor_applied"]

    def test_normal_deficit(self):
        r = build_targets(intake(sex="male", age=35, height_cm=180, weight_kg=90, activity="moderate"))
        assert r["daily_calories"] == 2325 and r["warnings"] == []
        assert r["protein_g"] == round(90 * 1.8)

    def test_pace_is_capped_at_one_percent_of_body_weight(self):
        r = build_targets(intake(weight_kg=70, weekly_pace_kg=1.0, sex="male", height_cm=180, activity="moderate"))
        assert r["weekly_pace_kg"] == 0.7
        assert "pace_capped" in [w["code"] for w in r["warnings"]]

    def test_no_deficit_when_pregnant_or_breastfeeding(self):
        for flag in ("pregnant", "breastfeeding"):
            r = build_targets(intake(**{flag: True}, activity="moderate"))
            assert r["goal"] == "maintain" and r["daily_calories"] >= r["tdee"] - 1
            assert "no_deficit" in [w["code"] for w in r["warnings"]]

    def test_medical_condition_is_flagged_for_professional_review(self):
        r = build_targets(intake(medical_conditions=True))
        assert "professional_review" in [w["code"] for w in r["warnings"]]

    def test_gain_goal_adds_calories(self):
        base = build_targets(intake(goal="maintain", activity="moderate", sex="male", height_cm=180, weight_kg=75))
        gain = build_targets(intake(goal="gain", activity="moderate", sex="male", height_cm=180, weight_kg=75))
        assert gain["daily_calories"] > base["daily_calories"]

    def test_keto_sets_a_low_carb_target_and_a_carb_capped_rule(self):
        r = build_targets(intake(regimes=["keto"], sex="male", height_cm=180, weight_kg=90, activity="moderate"))
        assert r["carbs_g"] == 25
        rule = r["shield_profile"]["regimes"][0]
        assert rule["code"] == "keto" and rule["max_item_carbs_g"] == 12 and "bread" in rule["block_ingredients"]

    def test_per_meal_budgets_add_up_to_the_day(self):
        r = build_targets(intake(sex="male", age=35, height_cm=180, weight_kg=90, activity="moderate"))
        assert abs(sum(r["per_meal"].values()) - r["daily_calories"]) <= 2

    def test_shield_profile_carries_allergies_and_the_daily_budget(self):
        r = build_targets(intake(allergies=["peanut", "tomato"], regimes=["gluten_free"]))
        sp = r["shield_profile"]
        assert sp["allergies"] == ["peanut", "tomato"] and sp["remaining_calories"] == r["daily_calories"]
        assert sp["strictness"] == "balanced"

    def test_arabic_warnings_and_disclaimer(self):
        r = build_targets(intake(), lang="ar")
        assert ARABIC.search(r["warnings"][0]["text"]) and ARABIC.search(r["disclaimer"]) and r["warnings"][0]["code"] == "floor_applied"

    def test_the_result_works_as_a_shield_profile(self):
        from products.cymart.partners.engine import PartnerShieldEngine
        sp = build_targets(intake(allergies=["peanut"]))["shield_profile"]
        res = PartnerShieldEngine().evaluate(sp, [{"item_id": "x", "ingredients": ["peanut sauce"]}])
        assert res.overall == "hard_block"


def meal(item_id, name, calories, carbs, ingredients, types, tags=(), mods=None, **kw):
    d = {"item_id": item_id, "name": name, "restaurant": kw.get("restaurant", "R"), "calories": calories, "carbs_g": carbs,
         "ingredients": ingredients, "diet_tags": list(tags), "meal_types": types}
    if mods:
        d["modifications"] = mods
    return d


PROFILE = {"allergies": ["peanut", "tomato"], "regimes": [{"code": "gluten_free", "block_ingredients": ["wheat", "bread"]}],
           "remaining_calories": 2000, "strictness": "balanced"}
PER_MEAL = {"breakfast": 500, "lunch": 600, "dinner": 600, "snack": 300}
GF = ["gluten_free"]
POOL = [
    meal("oats", "Oat Bowl", 420, 50, ["oats", "milk"], ["breakfast"], GF),
    meal("eggs", "Egg Plate", 380, 4, ["egg", "spinach"], ["breakfast"], GF),
    meal("yog", "Yogurt Cup", 300, 20, ["yogurt", "berries"], ["breakfast", "snack"], GF),
    meal("l1", "Chicken Rice", 580, 45, ["chicken", "rice"], ["lunch", "dinner"], GF),
    meal("l2", "Grilled Fish", 520, 5, ["fish", "lemon"], ["lunch", "dinner"], GF),
    meal("l3", "Lamb Kofta", 590, 8, ["lamb", "onion"], ["lunch", "dinner"], GF),
    meal("l4", "Lentil Soup", 450, 40, ["lentils", "carrot"], ["lunch", "dinner"], GF),
    meal("l5", "Beef Bowl", 560, 30, ["beef", "rice"], ["lunch", "dinner"], GF),
    meal("sn1", "Almonds", 200, 6, ["almonds"], ["snack"], GF),
    meal("sn2", "Fruit Cup", 150, 30, ["apple", "orange"], ["snack"], GF),
    meal("bad1", "Satay Plate", 500, 10, ["chicken", "peanut sauce"], ["lunch", "dinner"], GF),
    meal("bad2", "Mystery Meal", 500, 10, [], ["lunch", "dinner"], GF),
    meal("big", "Giant Platter", 1400, 80, ["beef", "rice"], ["lunch", "dinner"], GF),
]
for p in POOL:
    if p["item_id"] == "bad2":
        p.pop("ingredients")


class TestWeek:
    def test_every_slot_of_the_week_is_filled_with_items_that_fit(self):
        w = plan_week(PROFILE, PER_MEAL, POOL)
        assert len(w["days"]) == 7 and w["summary"]["empty"] == 0 and w["summary"]["filled"] == 28
        by_id = {p["item_id"]: p for p in POOL}
        for day in w["days"]:
            for slot in day["slots"]:
                it = slot["item"]
                assert it["calories"] <= slot["budget_calories"]
                assert it["item_id"] not in ("bad1", "bad2", "big")          # allergen, unknown ingredients, over budget
                types = by_id[it["item_id"]]["meal_types"]
                assert slot["meal"] in types

    def test_variety(self):
        w = plan_week(PROFILE, PER_MEAL, POOL)
        for slot in ("lunch", "dinner"):
            ids = [next(s["item"]["item_id"] for s in d["slots"] if s["meal"] == slot) for d in w["days"]]
            assert all(len(set(ids[i:i + 3])) == 3 for i in range(len(ids) - 2))     # no repeat inside 3 days
            assert max(ids.count(i) for i in set(ids)) <= 2

    def test_no_item_repeats_within_one_day(self):
        w = plan_week(PROFILE, PER_MEAL, POOL)
        for day in w["days"]:
            ids = [s["item"]["item_id"] for s in day["slots"] if s["item"]]
            assert len(ids) == len(set(ids))

    def test_alternatives_are_runners_up(self):
        w = plan_week(PROFILE, PER_MEAL, POOL)
        for day in w["days"]:
            for s in day["slots"]:
                alts = [a["item_id"] for a in s["alternatives"]]
                assert len(alts) <= 2 and s["item"]["item_id"] not in alts

    def test_summary_counts_items_usable_in_at_least_one_meal(self):
        s = plan_week(PROFILE, PER_MEAL, POOL, days=1)["summary"]
        assert s["items_considered"] == 13 and s["items_usable"] == 10
        assert sum(s["hidden_by_plan"].values()) == 3 and s["hidden_by_plan"].get("calorie_budget_exceeded") == 1

    def test_hidden_counts_say_why(self):
        h = plan_week(PROFILE, PER_MEAL, POOL, days=1)["summary"]["hidden_by_plan"]
        assert h.get("allergen_conflict") == 1 and h.get("ingredients_unknown") == 1

    def test_a_slot_with_nothing_that_fits_is_empty_not_unsafe(self):
        only_bad = [p for p in POOL if p["item_id"] in ("bad1", "bad2", "big")]
        w = plan_week(PROFILE, PER_MEAL, only_bad, days=2)
        assert w["summary"]["filled"] == 0
        assert all(s["item"] is None and s["reason"] == "nothing_fits" for d in w["days"] for s in d["slots"])

    def test_item_one_removal_away_is_planned_with_the_change(self):
        pool = [meal("c", "Classic Burger", 700, 20, ["beef", "tomato", "lettuce"], ["lunch"], GF, mods=[{"ingredient": "tomato", "action": "remove"}])]
        w = plan_week(PROFILE, {"lunch": 800}, pool, days=1, slots=("lunch",))
        slot = w["days"][0]["slots"][0]
        assert slot["item"]["item_id"] == "c" and slot["item"]["changes"] == [{"type": "remove", "ingredient": "tomato", "replacement": None}]

    def test_days_and_deterministic(self):
        a = plan_week(PROFILE, PER_MEAL, POOL, days=3)
        assert len(a["days"]) == 3 and a == plan_week(PROFILE, PER_MEAL, POOL, days=3)

    def test_strict_mode_never_plans_what_balanced_would_warn_about(self):
        w = plan_week({**PROFILE, "strictness": "strict"}, PER_MEAL, POOL, days=2)
        assert all(s["item"]["calories"] <= s["budget_calories"] for d in w["days"] for s in d["slots"])

    def test_arabic_notes(self):
        w = plan_week(PROFILE, PER_MEAL, [p for p in POOL if p["item_id"] == "big"], days=1, lang="ar")
        assert ARABIC.search(w["days"][0]["slots"][0]["text"]) and ARABIC.search(w["notes"][0])


GROC = [
    {"item_id": "chk", "name": "Chicken Breast", "category": "protein", "servings": 4, "calories": 600, "carbs_g": 0, "ingredients": ["chicken"], "diet_tags": GF},
    {"item_id": "tof", "name": "Tofu", "category": "protein", "servings": 4, "calories": 500, "carbs_g": 6, "ingredients": ["soy"], "diet_tags": GF},
    {"item_id": "veg", "name": "Veg Box", "category": "vegetables", "servings": 7, "calories": 300, "carbs_g": 30, "ingredients": ["mixed vegetables"], "diet_tags": GF},
    {"item_id": "yog", "name": "Greek Yogurt", "category": "dairy", "servings": 4, "calories": 400, "carbs_g": 20, "ingredients": ["yogurt"], "diet_tags": GF},
    {"item_id": "pb", "name": "Peanut Butter", "category": "fats", "servings": 10, "calories": 900, "carbs_g": 20, "ingredients": ["peanut"], "diet_tags": GF},
    {"item_id": "oil", "name": "Olive Oil", "category": "fats", "servings": 20, "calories": 2000, "carbs_g": 0, "ingredients": ["olive oil"], "diet_tags": GF},
    {"item_id": "rice", "name": "Basmati Rice", "category": "grains", "servings": 10, "calories": 1400, "carbs_g": 300, "ingredients": ["rice"], "diet_tags": GF},
    {"item_id": "app", "name": "Apples", "category": "fruit", "servings": 7, "calories": 350, "carbs_g": 80, "ingredients": ["apple"], "diet_tags": GF},
    {"item_id": "alm", "name": "Almonds", "category": "snacks", "servings": 7, "calories": 700, "carbs_g": 20, "ingredients": ["almonds"], "diet_tags": GF},
]


class TestBasket:
    PROF = {"allergies": ["peanut"], "regimes": [], "strictness": "balanced"}

    def test_packs_cover_the_servings_needed(self):
        b = build_basket(self.PROF, GROC, 14000, needs={"protein": 14, "vegetables": 14, "dairy": 7, "fats": 7, "grains": 14, "fruit": 7, "snacks": 7})
        line = {l["category"]: l for l in b["lines"]}
        assert line["protein"]["packs"] == 4 and line["protein"]["servings"] == 16        # ceil(14 / 4)
        assert line["vegetables"]["packs"] == 2

    def test_allergen_items_are_never_chosen_and_a_safe_alternative_is(self):
        b = build_basket(self.PROF, GROC, 14000)
        fats = next(l for l in b["lines"] if l["category"] == "fats")
        assert fats["item_id"] == "oil"
        assert b["hidden_by_plan"].get("allergen_conflict") == 1

    def test_keto_drops_grains(self):
        keto = {"allergies": [], "regimes": [{"code": "keto", "max_item_carbs_g": 12}], "strictness": "balanced"}
        assert "grains" not in weekly_needs(keto) and weekly_needs(keto)["fruit"] == 2

    def test_override_and_gaps(self):
        b = build_basket(self.PROF, [g for g in GROC if g["category"] != "dairy"], 14000, needs={"dairy": 7, "grains": 0})
        assert any(g["category"] == "dairy" and g["reason"] == "no_items" for g in b["gaps"])
        assert "grains" not in b["needs"]

    def test_nothing_fits_is_a_gap_not_a_unsafe_pick(self):
        only_pb = [g for g in GROC if g["item_id"] == "pb"]
        b = build_basket(self.PROF, only_pb, 14000, needs={"fats": 7})
        assert b["lines"] == []
        assert next(g for g in b["gaps"] if g["category"] == "fats")["reason"] == "nothing_fits"

    def test_basket_is_checked_as_one_basket_against_the_week(self):
        ok = build_basket(self.PROF, GROC, 20000)
        tight = build_basket(self.PROF, GROC, 1500)
        assert ok["totals"]["within_budget"] is True and tight["totals"]["within_budget"] is False

    def test_arabic_gap_text(self):
        b = build_basket(self.PROF, [], 14000, needs={"protein": 7}, lang="ar")
        assert ARABIC.search(b["gaps"][0]["text"])


@pytest.mark.django_db
class TestPlannerApi:
    def _client(self):
        _, raw = Partner.create_with_key("Planner Platform")
        c = APIClient()
        c.credentials(HTTP_X_API_KEY=raw)
        return c

    def test_requires_api_key(self):
        for path in ("targets", "week", "basket"):
            assert APIClient().post(f"/api/v1/partner/plan/{path}/", {}, format="json").status_code == 403

    def test_targets_end_to_end_and_plan_feeds_the_week(self):
        c = self._client()
        t = c.post("/api/v1/partner/plan/targets/", {"intake": intake(allergies=["peanut", "tomato"], regimes=["gluten_free"]), "language": "en"}, format="json")
        assert t.status_code == 200
        targets = t.json()
        w = c.post("/api/v1/partner/plan/week/", {"shield_profile": targets["shield_profile"], "per_meal": targets["per_meal"], "pool": POOL, "days": 7}, format="json")
        assert w.status_code == 200, w.content
        assert w.json()["summary"]["filled"] > 0

    def test_under_18_is_refused(self):
        r = self._client().post("/api/v1/partner/plan/targets/", {"intake": intake(age=16)}, format="json")
        assert r.status_code == 400 and "adults" in r.content.decode()

    def test_validation(self):
        c = self._client()
        assert c.post("/api/v1/partner/plan/targets/", {"intake": {"sex": "male"}}, format="json").status_code == 400
        base = {"shield_profile": PROFILE, "per_meal": PER_MEAL, "pool": POOL}
        assert c.post("/api/v1/partner/plan/week/", {**base, "pool": []}, format="json").status_code == 400
        assert c.post("/api/v1/partner/plan/week/", {**base, "per_meal": {"brunch": 400}}, format="json").status_code == 400
        assert c.post("/api/v1/partner/plan/week/", {**base, "days": 30}, format="json").status_code == 400
        assert c.post("/api/v1/partner/plan/basket/", {"shield_profile": PROFILE, "pool": GROC}, format="json").status_code == 400

    def test_basket_endpoint(self):
        r = self._client().post("/api/v1/partner/plan/basket/", {"shield_profile": {"allergies": ["peanut"]}, "weekly_calories": 14000, "pool": GROC}, format="json")
        assert r.status_code == 200 and r.json()["lines"]


@pytest.mark.django_db
class TestMealTimeTrigger:
    CANDS = [
        {"item_id": "bunless", "name": "Bunless Burger", "restaurant": "Burger House", "price": 5.0, "calories": 560, "carbs_g": 6,
         "ingredients": ["beef", "lettuce"], "diet_tags": ["keto"]},
        {"item_id": "salad", "name": "Greek Salad", "restaurant": "Green Bowl", "price": 4.0, "calories": 320, "carbs_g": 12,
         "ingredients": ["lettuce", "feta"], "diet_tags": ["keto"]},
        {"item_id": "satay", "name": "Satay Burger", "restaurant": "Grill Bar", "price": 5.5, "calories": 640, "carbs_g": 12,
         "ingredients": ["chicken", "peanut sauce"], "diet_tags": ["keto"]},
    ]
    PROFILE = {"allergies": ["peanut", "tomato"], "regimes": [{"code": "keto", "max_item_carbs_g": 15}], "remaining_calories": 900}

    def _client(self):
        _, raw = Partner.create_with_key("Trigger Platform")
        c = APIClient()
        c.credentials(HTTP_X_API_KEY=raw)
        return c

    def _start(self, c, **kw):
        body = {"profile": self.PROFILE, "platform_tools": ["search_menu", "add_to_cart", "view_cart", "checkout"],
                "trigger": {"type": "meal_time", "meal": "lunch", "calories": 550, "candidates": self.CANDS}, **kw}
        return c.post("/api/v1/partner/agent/turn/", body, format="json")

    def test_a_meal_time_prompt_offers_the_planned_options_that_fit(self):
        r = self._start(self._client())
        assert r.status_code == 200
        out = r.json()
        assert out["status"] == "reply"
        assert out["reply"].startswith("It's time for lunch.")
        assert "Bunless Burger" in out["reply"] and "Greek Salad" in out["reply"]
        assert "Satay" not in out["reply"]                         # peanut: hidden
        assert "550 kcal target" in out["reply"]                  # ranked against this meal's budget
        assert out["new_messages"][0]["content"] == "[meal_time:lunch]"

    def test_the_customer_then_chooses_and_the_order_is_shielded_as_usual(self, client):
        p = FakePlatform(client, profile=self.PROFILE, menu=self.CANDS)
        out = p.client.post("/api/v1/partner/agent/turn/", {"profile": self.PROFILE, "platform_tools": ALL, "trigger": {
            "type": "meal_time", "meal": "lunch", "calories": 550, "candidates": self.CANDS}}, format="json").json()
        p.messages = list(out["new_messages"])
        reply = p.say("Greek Salad")
        assert "Added Greek Salad" in reply["reply"] and p.cart[0]["item_id"] == "salad"
        assert "ALLERGY" in p.notes_seen[0]
        p.say("confirm")
        assert p.checked_out

    def test_a_blocked_candidate_cannot_be_added_even_if_it_was_planned(self, client):
        p = FakePlatform(client, profile=self.PROFILE, menu=self.CANDS)
        out = p.client.post("/api/v1/partner/agent/turn/", {"profile": self.PROFILE, "platform_tools": ALL, "trigger": {
            "type": "meal_time", "meal": "lunch", "candidates": self.CANDS}}, format="json").json()
        p.messages = list(out["new_messages"])
        p.say("Satay Burger")
        assert p.cart == []

    def test_arabic_meal_prompt(self):
        r = self._start(self._client(), language="ar")
        assert r.json()["reply"].startswith("حان وقت الغداء.")

    def test_trigger_validation(self):
        c = self._client()
        msg = [{"role": "user", "content": "hi"}]
        assert self._start(c, messages=msg).status_code == 400            # a trigger starts a new conversation
        assert c.post("/api/v1/partner/agent/turn/", {"profile": {}, "messages": []}, format="json").status_code == 400
        bad = {"profile": {}, "trigger": {"type": "meal_time", "meal": "brunch", "candidates": []}}
        assert c.post("/api/v1/partner/agent/turn/", bad, format="json").status_code == 400


ALL = ["search_menu", "add_to_cart", "view_cart", "checkout"]


@pytest.fixture
def client(db):
    _, raw = Partner.create_with_key("Trigger Platform 2")
    c = APIClient()
    c.credentials(HTTP_X_API_KEY=raw)
    return c
