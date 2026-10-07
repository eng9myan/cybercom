"""Allergen groups: what a customer means when they say "gluten", "dairy" or "nuts".

Ingredient lists name ingredients ("wheat bun", "cheese", "almonds"), customers name allergens ("gluten", "dairy", "nuts").
Without a map between the two, the word "gluten" would not catch "wheat bun". This module is that map.

How an allergy is matched:

  * A word that names a group (or one of its aliases) is expanded to everything in that group, in English and Arabic.
  * A word that is not a group is matched as before: as text, in either direction ("peanut" catches "peanut sauce").
  * Group terms match inside an ingredient name ("cheese" in "mozzarella cheese"); a few very short or ambiguous terms
    ("flour", "bread", "bun") match only when the whole ingredient is exactly that word, so "rice flour" is not caught.
  * Known harmless look-alikes are exempted for that group only ("eggplant" for egg, "peanut butter" and "almond milk" for dairy,
    "coconut" for nuts, anything labelled "gluten-free" for gluten). The exemptions are short, listed below and tested.

It errs on the side of blocking: a customer who types an allergy we do not know still gets plain text matching, and a group
is only ever widened. It is a starting list for the platform's nutrition team to review, not a clinical or legal list. An
ingredient that is not listed on the item at all cannot be found by any map; that is what the "ingredients unknown" check is for.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from .i18n import normalise

# term lists: `terms` match inside an ingredient name; `exact` match only the whole ingredient name; `exempt` phrases are
# removed from an ingredient before this group's terms are looked for.
GROUPS: dict[str, dict] = {
    "gluten": {
        "aliases": ["gluten", "celiac", "coeliac", "gluten free", "gluten-free", "غلوتين", "جلوتين", "حساسية القمح", "سيلياك"],
        "terms": ["wheat", "gluten", "barley", "rye", "spelt", "semolina", "couscous", "bulgur", "freekeh", "farro", "durum", "malt",
                  "seitan", "kamut", "triticale", "breadcrumb", "crouton",
                  "قمح", "غلوتين", "جلوتين", "شعير", "شيلم", "سميد", "كسكس", "برغل", "فريكة", "شعيرية"],
        "exact": ["flour", "bread", "pasta", "noodles", "bun", "buns", "dough", "crackers", "biscuit", "biscuits", "pastry", "tortilla", "pita",
                  "pita bread", "naan", "roll", "rolls", "pizza dough", "cake", "طحين", "خبز", "معكرونة", "عجين", "كعك", "فطيرة"],
        "exempt": ["gluten free", "gluten-free", "maltodextrin", "maltitol", "maltose", "buckwheat", "خال من الغلوتين"],
    },
    "wheat": {
        "aliases": ["wheat", "قمح"],
        "terms": ["wheat", "semolina", "durum", "spelt", "couscous", "bulgur", "freekeh", "farro", "kamut", "seitan", "breadcrumb", "crouton",
                  "قمح", "سميد", "كسكس", "برغل", "فريكة"],
        "exact": ["flour", "bread", "pasta", "bun", "buns", "dough", "tortilla", "pita", "pita bread", "crackers", "طحين", "خبز", "معكرونة", "عجين"],
        "exempt": ["wheat free", "wheat-free", "buckwheat"],
    },
    "dairy": {
        "aliases": ["dairy", "milk", "lactose", "cow's milk", "cows milk", "milk protein", "milk products", "ألبان", "حليب", "لاكتوز", "منتجات الألبان"],
        "terms": ["milk", "cheese", "butter", "cream", "yogurt", "yoghurt", "yogourt", "whey", "casein", "ghee", "curd", "labneh", "laban", "paneer",
                  "mozzarella", "feta", "parmesan", "cheddar", "halloumi", "ricotta", "mascarpone", "custard", "lactose", "kefir", "gelato",
                  "brie", "gouda", "bechamel", "béchamel", "lactalbumin",
                  "حليب", "جبن", "زبدة", "قشطة", "كريمة", "لبن", "زبادي", "سمن", "لبنة", "موزاريلا", "فيتا", "بارميزان", "شيدر", "حلوم", "جبنة"],
        "exact": [],
        "exempt": ["peanut butter", "almond butter", "cocoa butter", "shea butter", "nut butter", "cashew butter", "sunflower butter", "seed butter",
                   "butternut", "butterscotch", "coconut milk", "coconut cream", "almond milk", "oat milk", "soy milk", "soya milk", "rice milk",
                   "cashew milk", "hazelnut milk", "cream of tartar", "dairy free", "dairy-free", "non dairy", "non-dairy",
                   "زبدة الفول السوداني", "زبدة اللوز", "حليب جوز الهند", "حليب اللوز", "حليب الصويا", "حليب الشوفان", "خال من الألبان"],
    },
    "egg": {
        "aliases": ["egg", "eggs", "بيض", "بيضة"],
        "terms": ["egg", "albumen", "albumin", "mayo", "mayonnaise", "aioli", "meringue", "hollandaise", "custard", "eggnog", "ovalbumin", "ovomucoid",
                  "بيض", "بيضة", "مايونيز", "ميرنغ"],
        "exact": [],
        "exempt": ["eggplant", "egg plant", "egg free", "egg-free", "eggfruit"],
    },
    "peanut": {
        "aliases": ["peanut", "peanuts", "groundnut", "groundnuts", "فول سوداني", "فستق عبيد"],
        "terms": ["peanut", "groundnut", "arachis", "monkey nut", "satay", "فول سوداني", "فستق عبيد"],
        "exact": [],
        "exempt": ["peanut free", "peanut-free"],
    },
    "tree_nut": {
        "aliases": ["tree nut", "tree nuts", "المكسرات", "مكسرات"],
        "terms": ["almond", "walnut", "cashew", "pistachio", "hazelnut", "pecan", "macadamia", "brazil nut", "pine nut", "chestnut", "praline",
                  "marzipan", "nutella", "gianduja", "nougat", "mixed nuts", "nut mix", "trail mix", "frangipane", "amaretto",
                  "لوز", "جوز", "كاجو", "فستق", "بندق", "بيكان", "مكاداميا", "صنوبر", "كستناء"],
        "exact": ["nuts", "nut", "مكسرات"],
        "exempt": ["coconut", "nutmeg", "nut free", "nut-free", "nuts free", "جوز الهند", "جوز الطيب"],
    },
    "shellfish": {
        "aliases": ["shellfish", "crustacean", "crustaceans", "mollusc", "mollusk", "molluscs", "mollusks", "shrimp", "prawn", "prawns", "shrimps",
                    "محار", "روبيان", "جمبري", "قشريات", "رخويات"],
        "terms": ["shellfish", "shrimp", "prawn", "crab", "lobster", "crayfish", "crawfish", "langoustine", "krill", "scampi", "squid", "calamari",
                  "octopus", "clam", "mussel", "oyster", "scallop", "escargot", "abalone", "cuttlefish",
                  "روبيان", "جمبري", "سلطعون", "كابوريا", "استاكوزا", "حبار", "أخطبوط", "محار", "بلح البحر", "قشريات"],
        "exact": ["snail", "snails"],
        "exempt": ["oyster mushroom", "crab apple", "crabapple", "فطر المحار"],
    },
    "fish": {
        "aliases": ["fish", "سمك", "أسماك"],
        "terms": ["fish", "salmon", "tuna", "cod", "anchovy", "anchovies", "sardine", "mackerel", "trout", "tilapia", "haddock", "herring", "halibut",
                  "pollock", "snapper", "sea bass", "worcestershire", "caviar", "surimi", "swordfish", "pangasius",
                  "سمك", "سلمون", "تونة", "ساردين", "أنشوجة", "ماكريل", "هامور", "سمك"],
        "exact": ["bass", "roe", "sole"],
        "exempt": ["fish free", "fish-free", "jellyfish"],
    },
    "soy": {
        "aliases": ["soy", "soya", "soybean", "soybeans", "صويا", "فول الصويا"],
        "terms": ["soy", "soya", "soybean", "tofu", "tempeh", "edamame", "miso", "natto", "tamari", "shoyu", "صويا", "توفو"],
        "exact": [],
        "exempt": ["soy free", "soy-free"],
    },
    "sesame": {
        "aliases": ["sesame", "سمسم"],
        "terms": ["sesame", "tahini", "tahina", "halva", "halvah", "hummus", "za'atar", "zaatar", "gomasio", "benne", "سمسم", "طحينة", "طحينية"],
        "exact": [],
        "exempt": ["sesame free", "sesame-free"],
    },
    "mustard": {"aliases": ["mustard", "خردل"], "terms": ["mustard", "خردل"], "exact": [], "exempt": []},
    "celery": {"aliases": ["celery", "celeriac", "كرفس"], "terms": ["celery", "celeriac", "كرفس"], "exact": [], "exempt": []},
    "lupin": {"aliases": ["lupin", "lupine", "ترمس"], "terms": ["lupin", "lupine", "ترمس"], "exact": [], "exempt": []},
    "sulphites": {"aliases": ["sulphite", "sulphites", "sulfite", "sulfites", "كبريتيت"],
                  "terms": ["sulphite", "sulfite", "sulphur dioxide", "sulfur dioxide", "كبريتيت"], "exact": [], "exempt": []},
}

# a single word that means several groups
COMBINED = {
    "nuts": ["peanut", "tree_nut"], "nut": ["peanut", "tree_nut"], "nut allergy": ["peanut", "tree_nut"], "مكسرات": ["peanut", "tree_nut"],
    "seafood": ["shellfish", "fish"], "مأكولات بحرية": ["shellfish", "fish"], "المأكولات البحرية": ["shellfish", "fish"],
}

# typed word -> groups, built once (normalised the way ingredients are)
_ALIAS: dict[str, list[str]] = {}
for _g, _spec in GROUPS.items():
    for _a in _spec["aliases"]:
        _ALIAS.setdefault(normalise(_a), []).append(_g)
for _a, _gs in COMBINED.items():
    _ALIAS[normalise(_a)] = list(_gs)


@dataclass(frozen=True)
class _Entry:
    typed: str            # the allergy as the customer typed it (what we echo back)
    term: str             # normalised text to look for
    exact: bool = False   # True: the whole ingredient must equal `term`
    both_ways: bool = False  # plain typed words also match when the ingredient is inside the word (the original rule)
    exempt: tuple = ()


class Allergies:
    """A customer's allergies, expanded into everything an ingredient list might call them."""

    def __init__(self, values):
        entries: list[_Entry] = []
        self.names: list[str] = []
        seen_typed: set[str] = set()
        for raw in values or []:
            typed = str(raw).strip()
            key = normalise(typed)
            if not key or key in seen_typed:
                continue
            seen_typed.add(key)
            self.names.append(typed)
            groups = _ALIAS.get(key, [])
            covered = False
            for g in groups:
                spec = GROUPS[g]
                exempt = tuple(normalise(e) for e in spec["exempt"])
                for term in spec["terms"]:
                    entries.append(_Entry(typed, normalise(term), exempt=exempt))
                    covered = covered or normalise(term) == key
                for term in spec["exact"]:
                    entries.append(_Entry(typed, normalise(term), exact=True, exempt=exempt))
                    covered = covered or normalise(term) == key
            if not covered:                      # the plain rule, exactly as before, for any word we do not map
                entries.append(_Entry(typed, key, both_ways=True))
        self.names.sort()
        self._entries = entries

    def __bool__(self):
        return bool(self._entries)

    def hits(self, ingredients) -> list[str]:
        """The allergies (as typed) that any of these normalised ingredient names trigger."""
        out: set[str] = set()
        for ing in ingredients:
            for e in self._entries:
                if e.typed in out:
                    continue
                text = ing
                for ex in e.exempt:
                    if ex in text:
                        text = text.replace(ex, " ")
                if e.exact:
                    ok = text == ing and ing.strip() == e.term
                else:
                    ok = e.term in text or (e.both_ways and text.strip() != "" and text.strip() in e.term)
                if ok:
                    out.add(e.typed)
        return sorted(out)


@lru_cache(maxsize=512)
def _build(values: tuple) -> Allergies:
    return Allergies(values)


def allergies_of(values) -> Allergies:
    """Cached: the same customer's allergy list is expanded once, not once per item."""
    return _build(tuple(str(v) for v in (values or [])))
