"""Allergen groups: "gluten" must catch "wheat bun", but a harmless look-alike must not hide a safe dish needlessly,
and no exemption may ever hide a real allergen."""
import pytest

from products.cymart.partners.allergens import GROUPS, Allergies, allergies_of
from products.cymart.partners.engine import PartnerShieldEngine
from products.cymart.partners.i18n import normalise


def hit(allergy, *ingredients):
    return bool(allergies_of([allergy]).hits({normalise(i) for i in ingredients}))


def verdict(allergies, ingredients, lang="en"):
    item = {"item_id": "x", "calories": 100, "carbs_g": 1, "ingredients": ingredients, "diet_tags": []}
    return PartnerShieldEngine(lang).check_item({"allergies": allergies, "regimes": [], "remaining_calories": None}, item)


class TestGroupsCatchWhatTheCustomerMeans:
    @pytest.mark.parametrize("allergy,ingredient", [
        ("gluten", "wheat bun"), ("gluten", "barley"), ("gluten", "rye bread"), ("gluten", "flour"), ("gluten", "bread"), ("gluten", "pasta"),
        ("gluten", "couscous"), ("celiac", "semolina"), ("coeliac", "bulgur"),
        ("wheat", "wheat flour"), ("wheat", "bread"),
        ("dairy", "cheese"), ("dairy", "mozzarella"), ("dairy", "butter"), ("dairy", "greek yogurt"), ("dairy", "cream"), ("dairy", "whey protein"),
        ("milk", "cheddar cheese"), ("lactose", "milk"),
        ("nuts", "almonds"), ("nuts", "walnuts"), ("nuts", "peanut sauce"), ("nuts", "mixed nuts (peanut)"), ("tree nuts", "cashew"),
        ("tree nut", "pistachio"), ("nuts", "hazelnut spread"),
        ("shellfish", "shrimp"), ("shellfish", "lobster tail"), ("shellfish", "crab"), ("shellfish", "calamari"), ("crustacean", "prawn"),
        ("shrimp", "prawn"), ("prawn", "shrimp"), ("seafood", "shrimp"), ("seafood", "salmon"),
        ("egg", "mayo"), ("egg", "mayonnaise"), ("eggs", "meringue"), ("egg", "egg yolk"),
        ("fish", "anchovy"), ("fish", "tuna"), ("fish", "salmon fillet"), ("fish", "fish sauce"), ("fish", "worcestershire sauce"),
        ("soy", "tofu"), ("soy", "soy sauce"), ("soya", "edamame"), ("soy", "miso"),
        ("sesame", "tahini"), ("sesame", "halva"), ("sesame", "hummus"),
        ("peanut", "groundnut oil"), ("peanuts", "satay sauce"),
        ("mustard", "dijon mustard"), ("celery", "celeriac"), ("lupin", "lupin flour"), ("sulphites", "sulfite"),
    ])
    def test_group_word_catches_member(self, allergy, ingredient):
        assert hit(allergy, ingredient), f"'{allergy}' should catch '{ingredient}'"

    def test_the_customers_own_word_is_what_we_echo_back(self):
        v = verdict(["dairy", "gluten"], ["cheese", "wheat bun"])
        assert v.severity == "hard_block" and v.matched == ["dairy", "gluten"]
        assert "dairy" in v.reason and "cheese" not in v.reason

    def test_every_group_hits_its_own_terms(self):
        for name, spec in GROUPS.items():
            a = allergies_of([spec["aliases"][0]])
            for term in spec["terms"]:
                assert a.hits({normalise(term)}), (name, term)
            for term in spec["exact"]:
                assert a.hits({normalise(term)}), (name, term)


class TestHarmlessLookAlikesAreNotBlocked:
    @pytest.mark.parametrize("allergy,ingredient", [
        ("egg", "eggplant"), ("egg", "eggplant"), ("dairy", "peanut butter"), ("dairy", "almond milk"), ("dairy", "coconut milk"),
        ("dairy", "cocoa butter"), ("dairy", "oat milk"), ("dairy", "butternut squash"), ("dairy", "cream of tartar"),
        ("nuts", "coconut"), ("nuts", "nutmeg"), ("tree nuts", "coconut milk"),
        ("gluten", "rice flour"), ("gluten", "corn flour"), ("gluten", "rice noodles"), ("gluten", "gluten-free pasta"),
        ("gluten", "gluten free bread"), ("gluten", "buckwheat"), ("gluten", "maltodextrin"),
        ("wheat", "buckwheat"), ("shellfish", "oyster mushroom"), ("shellfish", "crab apple"), ("fish", "jellyfish"),
        ("soy", "soy-free dressing"), ("peanut", "peanut free granola"), ("sesame", "sesame-free bread"),
    ])
    def test_not_blocked(self, allergy, ingredient):
        assert not hit(allergy, ingredient), f"'{allergy}' should NOT catch '{ingredient}'"


class TestNoExemptionHidesARealAllergen:
    @pytest.mark.parametrize("allergy,ingredients", [
        ("egg", ["eggplant", "egg"]),                       # an exempt look-alike next to the real thing
        ("egg", ["eggplant parmesan with mayo"]),
        ("dairy", ["peanut butter", "cheese"]),
        ("dairy", ["almond milk", "milk"]),
        ("nuts", ["coconut", "almond"]),
        ("tree nuts", ["coconut", "walnut"]),
        ("gluten", ["gluten-free pasta", "wheat bun"]),
        ("shellfish", ["oyster mushroom", "oyster sauce"]),
        ("dairy", ["butternut", "butter"]),
    ])
    def test_still_blocked(self, allergy, ingredients):
        assert hit(allergy, *ingredients), (allergy, ingredients)

    def test_exemptions_are_per_group(self):
        assert hit("nuts", "almond milk")          # almond milk is exempt for dairy, never for a nut allergy
        assert hit("tree nuts", "almond butter")
        assert not hit("dairy", "almond milk")
        assert hit("peanut", "peanut butter") and not hit("dairy", "peanut butter")


class TestUnknownWordsAndOldBehaviourAreKept:
    def test_a_word_that_is_not_a_group_is_matched_as_text_both_ways(self):
        assert hit("kiwi", "kiwi fruit") and hit("peanut sauce", "peanut")
        assert not hit("kiwi", "apple")

    def test_unknown_word_in_a_longer_name(self):
        assert hit("mango", "mango chutney")
        assert not hit("nut", "nut-free flour blend")      # 'nut' is now a group word, and "nut-free" is labelled as free of it

    def test_empty_and_duplicate_allergies(self):
        assert not Allergies([]) and not Allergies(["", "  "]) and not Allergies(None)
        a = Allergies(["Dairy", "dairy", "DAIRY"])
        assert a.names == ["Dairy"]

    def test_case_and_spacing_do_not_matter(self):
        assert hit("  GLUTEN ", "Wheat Bun")


class TestArabic:
    @pytest.mark.parametrize("allergy,ingredient", [
        ("غلوتين", "خبز القمح"), ("جلوتين", "شعير"), ("حليب", "جبنة"), ("ألبان", "زبدة"), ("ألبان", "لبن"), ("مكسرات", "لوز"),
        ("مكسرات", "صلصة الفول السوداني"), ("قشريات", "روبيان"), ("روبيان", "جمبري"), ("بيض", "مايونيز"), ("سمك", "سلمون"),
        ("سمسم", "طحينة"), ("صويا", "توفو"), ("فول سوداني", "صلصة الفول السوداني"),
    ])
    def test_arabic_group_word_catches_member(self, allergy, ingredient):
        assert hit(allergy, ingredient), (allergy, ingredient)

    @pytest.mark.parametrize("allergy,ingredient", [
        ("مكسرات", "جوز الهند"), ("ألبان", "حليب جوز الهند"), ("ألبان", "زبدة الفول السوداني"), ("مكسرات", "جوز الطيب"),
    ])
    def test_arabic_look_alikes(self, allergy, ingredient):
        assert not hit(allergy, ingredient)

    def test_arabic_reason_names_the_allergy_as_typed(self):
        v = verdict(["ألبان"], ["جبنة"], "ar")
        assert v.severity == "hard_block" and "ألبان" in v.reason


class TestEndToEnd:
    def test_gluten_allergy_blocks_a_wheat_bun_in_evaluate(self):
        v = verdict(["gluten"], ["beef", "wheat bun", "cheese"])
        assert v.severity == "hard_block" and v.code == "allergen_conflict"

    def test_gluten_free_pasta_is_fine_for_gluten(self):
        assert verdict(["gluten"], ["corn flour", "rice flour"]).severity == "allow"

    def test_unknown_ingredients_are_still_unverified(self):
        assert verdict(["dairy"], []).code == "ingredients_unknown"

    def test_prepare_uses_the_groups(self):
        from products.cymart.partners.prepare import KitchenInstructions
        item = {"item_id": "x", "calories": 500, "carbs_g": 10, "ingredients": ["beef", "cheese", "lettuce"], "diet_tags": [],
                "modifications": [{"ingredient": "cheese", "action": "remove"}]}
        r = KitchenInstructions("en").prepare({"allergies": ["dairy"], "regimes": [], "remaining_calories": None}, item)
        assert r.status == "ok_with_changes" and any(i["type"] == "remove" and i["ingredient"] == "cheese" for i in r.instructions)
        assert "DAIRY" in r.vendor_note.upper()

    def test_substitute_option_containing_the_group_is_not_chosen(self):
        from products.cymart.partners.prepare import KitchenInstructions
        item = {"item_id": "x", "calories": 500, "carbs_g": 10, "ingredients": ["chicken", "peanut sauce"], "diet_tags": [],
                "modifications": [{"ingredient": "peanut sauce", "action": "substitute",
                                   "options": [{"name": "almond dressing", "ingredients": ["almonds"]}, {"name": "herb dressing", "ingredients": ["herbs"]}]}]}
        r = KitchenInstructions("en").prepare({"allergies": ["nuts"], "regimes": [], "remaining_calories": None}, item)
        sub = [i for i in r.instructions if i["type"] == "substitute"]
        assert sub and sub[0]["replacement"] == "herb dressing"
