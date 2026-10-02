import re

import pytest
from rest_framework.test import APIClient

from products.cymart.partners.engine import PartnerShieldEngine
from products.cymart.partners.i18n import MESSAGES, normalise
from products.cymart.partners.models import Partner
from products.cymart.partners.prepare import KitchenInstructions
from products.cymart.partners.ranking import PartnerRanker

ARABIC = re.compile("[؀-ۿ]")

AR_SANDWICH = {
    "item_id": "ساندويتش-كلوب",
    "calories": 600,
    "carbs_g": 45,
    "ingredients": ["خبز القمح", "دجاج", "طماطم", "بصل", "خس"],
    "diet_tags": [],
    "modifications": [
        {"ingredient": "طماطم", "action": "remove"},
        {"ingredient": "بصل", "action": "remove"},
        {"ingredient": "خبز القمح", "action": "substitute", "makes": ["gluten_free"],
         "options": [{"name": "خبز خالٍ من الغلوتين", "ingredients": ["دقيق الأرز"]}, {"name": "لفافة خس"}]},
    ],
}
AR_PROFILE = {
    "allergies": ["طماطم", "بصل"],
    "regimes": [{"code": "gluten_free", "block_ingredients": ["خبز القمح", "قمح"]}],
}


class TestWording:
    def test_every_english_message_has_an_arabic_twin_with_the_same_placeholders(self):
        fmt = re.compile(r"\{(\w+)\}")
        assert set(MESSAGES["en"]) == set(MESSAGES["ar"])
        for key, en in MESSAGES["en"].items():
            ar = MESSAGES["ar"][key]
            assert {p.removesuffix("_u") for p in fmt.findall(en)} == {p for p in fmt.findall(ar)}, key
            if key != "ag_line":  # "2× name" is the same in both languages
                assert ARABIC.search(ar), key

    def test_english_wording_is_unchanged_by_default(self):
        profile = {"allergies": ["peanut"]}
        line = PartnerShieldEngine().evaluate(profile, [{"item_id": "1", "ingredients": ["peanut sauce"]}]).lines[0]
        assert line.reason == "Contains allergen(s): peanut."

    def test_unknown_language_falls_back_to_english(self):
        e = PartnerShieldEngine("fr")
        assert e.lang == "en"


class TestArabicMatching:
    @pytest.mark.parametrize("allergy,ingredient", [
        ("فستق", "صلصة الفستق"),
        ("فستق", "فُسْتُق"),          # with diacritics
        ("بيض", "بيضة"),                 # ta marbuta
        ("أرز", "ارز مطهو"),             # alef variants
        ("حليب", "حليب كامل الدسم"),
    ])
    def test_arabic_allergen_is_caught_however_it_is_typed(self, allergy, ingredient):
        res = PartnerShieldEngine("ar").evaluate({"allergies": [allergy]}, [{"item_id": "x", "ingredients": [ingredient]}])
        assert res.lines[0].severity == "hard_block"

    def test_normalise(self):
        assert normalise("  أُرْز ") == normalise("ارز")
        assert normalise("Peanut") == "peanut"

    def test_arabic_reason_and_codes(self):
        res = PartnerShieldEngine("ar").evaluate(
            {"allergies": ["فستق"]}, [{"item_id": "x", "ingredients": ["صلصة الفستق"]}])
        line = res.lines[0]
        assert line.code == "allergen_conflict"
        assert "يحتوي على" in line.reason and "فستق" in line.reason
        assert line.matched == ["فستق"]            # the partner's own spelling, echoed

    def test_arabic_regime_and_calorie_reasons(self):
        profile = {"regimes": [{"code": "keto", "max_item_carbs_g": 10}], "remaining_calories": 300}
        res = PartnerShieldEngine("ar").evaluate(profile, [{"item_id": "a", "carbs_g": 30, "diet_tags": ["keto"]},
                                                           {"item_id": "b", "calories": 500, "diet_tags": ["keto"]}])
        assert [ln.code for ln in res.lines] == ["regime_carb_limit", "calorie_budget_exceeded"]
        assert all(ARABIC.search(ln.reason) for ln in res.lines)

    def test_english_allergen_unaffected_by_arabic_normalisation(self):
        res = PartnerShieldEngine().evaluate({"allergies": ["Peanut"]}, [{"item_id": "x", "ingredients": ["PEANUT SAUCE"]}])
        assert res.lines[0].matched == ["Peanut"]


class TestArabicKitchenTicket:
    def test_full_arabic_ticket(self):
        res = KitchenInstructions("ar").prepare(AR_PROFILE, AR_SANDWICH)
        assert res.status == "ok_with_changes"
        assert res.verdict["severity"] == "allow"
        note = res.vendor_note
        assert "حضّر الطلب مع التعديلات التالية" in note
        assert "تنبيه حساسية" in note
        assert "بدون طماطم" in note and "بدون بصل" in note
        assert "استخدم خبز خالٍ من الغلوتين بدلًا من خبز القمح" in note
        assert "tomato" not in note.lower()
        assert res.instructions[0]["type"] == "allergy_alert" and ARABIC.search(res.instructions[0]["text"])
        assert "_note" not in res.instructions[0]

    def test_codes_and_structure_identical_in_both_languages(self):
        en_item = {**AR_SANDWICH}
        ar = KitchenInstructions("ar").prepare(AR_PROFILE, en_item)
        en = KitchenInstructions("en").prepare(AR_PROFILE, en_item)
        assert [(i["type"], i.get("ingredient"), i["reason_code"]) for i in ar.instructions] == \
               [(i["type"], i.get("ingredient"), i["reason_code"]) for i in en.instructions]
        assert ar.status == en.status

    def test_cannot_make_safe_in_arabic(self):
        item = {"item_id": "ساتاي", "calories": 300, "ingredients": ["دجاج", "صلصة الفول السوداني"]}
        res = KitchenInstructions("ar").prepare({"allergies": ["فول سوداني"]}, item)
        assert res.status == "cannot_make_safe"
        assert "لا يمكن التحضير" in res.vendor_note

    def test_unknown_ingredients_in_arabic(self):
        res = KitchenInstructions("ar").prepare({"allergies": ["فستق"]}, {"item_id": "س", "calories": 100})
        assert res.status == "needs_vendor_confirmation"
        assert "تأكّد من خلوّ الصنف" in res.vendor_note

    def test_arabic_option_with_allergen_in_its_ingredients_is_skipped(self):
        item = {"item_id": "x", "calories": 100, "ingredients": ["صلصة السمسم"], "diet_tags": [],
                "modifications": [{"ingredient": "صلصة السمسم", "action": "substitute", "options": [
                    {"name": "صلصة خاصة", "ingredients": ["سمسم"]}, {"name": "صلصة بيضاء"}]}]}
        res = KitchenInstructions("ar").prepare({"allergies": ["سمسم"]}, item)
        assert res.instructions[1]["replacement"] == "صلصة بيضاء"


class TestArabicRanking:
    def test_summary_in_arabic(self):
        profile = {"regimes": [{"code": "keto", "max_item_carbs_g": 15}], "meal_calories_target": 500}
        r = PartnerRanker("ar").rank(profile, [{"item_id": "a", "calories": 480, "carbs_g": 6, "diet_tags": ["keto"]}])
        assert ARABIC.search(r.ranked[0].summary)
        assert "سعرة" in r.ranked[0].summary and "كربوهيدرات" in r.ranked[0].summary


@pytest.mark.django_db
class TestLanguageParameterOverHttp:
    def _client(self):
        _, raw = Partner.create_with_key("Arabic Platform")
        c = APIClient()
        c.credentials(HTTP_X_API_KEY=raw)
        return c

    def test_evaluate_rank_prepare_accept_ar_and_echo_language(self):
        c = self._client()
        item = {"item_id": "x", "calories": 100, "ingredients": ["فستق"]}
        prof = {"allergies": ["فستق"]}
        ev = c.post("/api/v1/partner/evaluate/", {"profile": prof, "items": [item], "language": "ar"}, format="json").json()
        assert ev["language"] == "ar" and ARABIC.search(ev["lines"][0]["reason"])
        rk = c.post("/api/v1/partner/rank/", {"profile": {}, "items": [item], "language": "ar"}, format="json").json()
        assert rk["language"] == "ar"
        pr = c.post("/api/v1/partner/prepare/", {"profile": AR_PROFILE, "items": [AR_SANDWICH], "language": "ar"}, format="json").json()
        assert pr["language"] == "ar" and "بدون طماطم" in pr["vendor_note"]

    def test_default_is_english_and_invalid_language_is_rejected(self):
        c = self._client()
        body = {"profile": {"allergies": ["peanut"]}, "items": [{"item_id": "x", "ingredients": ["peanut"]}]}
        ev = c.post("/api/v1/partner/evaluate/", body, format="json").json()
        assert ev["language"] == "en" and ev["lines"][0]["reason"] == "Contains allergen(s): peanut."
        for path in ("evaluate", "rank", "prepare"):
            assert c.post(f"/api/v1/partner/{path}/", {**body, "language": "fr"}, format="json").status_code == 400

    def test_utf8_json_response(self):
        c = self._client()
        resp = c.post("/api/v1/partner/evaluate/", {"profile": {"allergies": ["فستق"]},
                      "items": [{"item_id": "x", "ingredients": ["فستق"]}], "language": "ar"}, format="json")
        assert "فستق" in resp.content.decode("utf-8")
