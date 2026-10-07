"""The Diet Shield engine — a stateless, catalog-agnostic evaluator.
Nothing here reads or writes a partner's own data; every call carries
everything it needs (the user's diet profile and the items to check) and
returns a verdict. Three gates, in order, overall result is the
strictest of the three:

    1. Safety   — allergy conflicts. Always a hard block, regardless of
                  the caller's strictness setting — never overridable.
    2. Regime   — composition rules (keto, halal, vegan, gluten-free,
                  diabetic-friendly, or any custom rule a partner
                  defines) — data the partner sends, not hardcoded here.
    3. Quantity — the item against the user's remaining calorie budget.

Each verdict carries a machine-readable ``code`` (so the partner can
localize the message in its own UI, e.g. Arabic) alongside an English
``reason``. If an item is not allowed and the caller supplied
``alternatives`` for it, the first alternative that passes every gate is
returned as ``swap`` — the engine never invents products, it only picks
from candidates the partner's own catalog offered.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .allergens import allergies_of
from .i18n import join_list, normalise, t

_SEVERITY_RANK = {"allow": 0, "warn": 1, "block": 2, "hard_block": 3}

# Stable verdict codes — part of the public API contract.
CODE_OK = "ok"
CODE_ALLERGEN = "allergen_conflict"
CODE_REGIME_INGREDIENT = "regime_blocked_ingredient"
CODE_REGIME_CARBS = "regime_carb_limit"
CODE_REGIME_TAG = "regime_not_compatible"
CODE_CALORIES = "calorie_budget_exceeded"
CODE_UNVERIFIED = "ingredients_unknown"


def _tokens(values) -> set[str]:
    """Normalised (lower-case, Arabic-aware) names, so "Peanut", "peanut" and
    Arabic spellings with or without diacritics compare equal."""
    return {n for n in (normalise(v) for v in (values or [])) if n}


def _originals(values) -> dict[str, str]:
    """normalised name -> the name as the partner sent it (what we echo back)."""
    out: dict[str, str] = {}
    for v in values or []:
        n = normalise(v)
        if n:
            out.setdefault(n, str(v).strip())
    return out


def _allergy_hit(allergies: set[str], ingredients: set[str]) -> set[str]:
    """Substring-aware, unlike the exact-token regime matching below:
    missing a real allergen is dangerous, so "peanut" must also catch an
    ingredient listed as "peanut sauce" or "mixed nuts (peanut)", not
    just an exact "peanut" token."""
    hits = set()
    for allergy in allergies:
        for ingredient in ingredients:
            if allergy in ingredient or ingredient in allergy:
                hits.add(allergy)
    return hits


@dataclass
class PartnerLineVerdict:
    item_id: str
    severity: str  # "allow" | "warn" | "block" | "hard_block"
    code: str = CODE_OK
    reason: str = ""
    matched: list[str] = field(default_factory=list)
    swap: dict | None = None  # {"item_id": ...} — first passing alternative

    @property
    def allowed(self) -> bool:
        return _SEVERITY_RANK[self.severity] <= _SEVERITY_RANK["warn"]


@dataclass
class PartnerEvaluation:
    overall: str
    lines: list[PartnerLineVerdict] = field(default_factory=list)

    @property
    def allowed(self) -> bool:
        return _SEVERITY_RANK[self.overall] <= _SEVERITY_RANK["warn"]


class PartnerShieldEngine:
    def __init__(self, lang: str = "en"):
        self.lang = lang if lang in ("en", "ar") else "en"

    def evaluate(
        self, profile: dict, items: list[dict], cumulative: bool = False
    ) -> PartnerEvaluation:
        """profile: {"allergies": [...], "regimes": [{"code", "block_ingredients":
        [...], "max_item_carbs_g": number|None}], "remaining_calories":
        number|None, "strictness": "strict"|"balanced"|"coach"}.
        items: [{"item_id", "calories", "carbs_g", "ingredients": [...],
        "diet_tags": [...], "alternatives": [<same shape, no nesting>]}].
        ``calories`` is the line total (per-unit calories x quantity).

        cumulative=False (default): every item is checked on its own
        against remaining_calories — right for a menu, where items are
        options, not a basket. cumulative=True: items are a cart, checked
        in order, and each item that passes uses up part of the remaining
        budget before the next is checked."""
        strictness = profile.get("strictness", "balanced")
        allergies = allergies_of(profile.get("allergies"))
        regimes = profile.get("regimes") or []
        remaining = profile.get("remaining_calories")

        lines = []
        for item in items:
            verdict = self._evaluate_item(item, allergies, regimes, remaining, strictness)
            if cumulative and remaining is not None and verdict.severity == "allow":
                remaining = float(remaining) - float(item.get("calories", 0))
            if verdict.severity != "allow":
                for alt in item.get("alternatives") or []:
                    alt_verdict = self._evaluate_item(alt, allergies, regimes, remaining, strictness)
                    if alt_verdict.severity == "allow":
                        verdict.swap = {"item_id": str(alt.get("item_id", ""))}
                        break
            lines.append(verdict)

        overall = max(
            (ln.severity for ln in lines), key=lambda s: _SEVERITY_RANK[s], default="allow"
        )
        return PartnerEvaluation(overall=overall, lines=lines)

    def check_item(self, profile: dict, item: dict) -> PartnerLineVerdict:
        """One item against one profile, on its own (no basket budget, no
        swap lookup) — the building block /rank/ filters with."""
        return self._evaluate_item(
            item, allergies_of(profile.get("allergies")), profile.get("regimes") or [],
            profile.get("remaining_calories"), profile.get("strictness", "balanced"),
        )

    def _soft(self, strictness: str) -> str:
        return "block" if strictness == "strict" else "warn"

    def _evaluate_item(self, item, allergies, regimes, remaining, strictness) -> PartnerLineVerdict:
        item_id = str(item.get("item_id", ""))
        ingredients = _tokens(item.get("ingredients"))
        ing_orig = _originals(item.get("ingredients"))
        diet_tags = _tokens(item.get("diet_tags"))
        lang = self.lang

        if allergies:
            matched = allergies.hits(ingredients)
            if matched:
                return PartnerLineVerdict(
                    item_id, "hard_block", CODE_ALLERGEN,
                    t(lang, CODE_ALLERGEN, matched=join_list(lang, matched)), matched,
                )

        # No ingredient list means the allergy check above had nothing to
        # check — that must never read as "safe". Report it as unverified
        # (a soft verdict: we can't claim a conflict we can't see).
        if allergies and not ingredients:
            return PartnerLineVerdict(
                item_id, self._soft(strictness), CODE_UNVERIFIED,
                t(lang, CODE_UNVERIFIED),
            )

        for regime in regimes:
            code = str(regime.get("code", "")).lower()
            blocked = _tokens(regime.get("block_ingredients")) & ingredients
            if blocked:
                matched = sorted(ing_orig.get(b, b) for b in blocked)
                return PartnerLineVerdict(
                    item_id, self._soft(strictness), CODE_REGIME_INGREDIENT,
                    t(lang, CODE_REGIME_INGREDIENT, regime=code, matched=join_list(lang, matched)), matched,
                )
            max_carbs = regime.get("max_item_carbs_g")
            if max_carbs is not None and float(item.get("carbs_g", 0)) > float(max_carbs):
                return PartnerLineVerdict(
                    item_id, self._soft(strictness), CODE_REGIME_CARBS,
                    t(lang, CODE_REGIME_CARBS, regime=code), [code],
                )
            if code and code not in diet_tags:
                return PartnerLineVerdict(
                    item_id, self._soft(strictness), CODE_REGIME_TAG,
                    t(lang, CODE_REGIME_TAG, regime=code), [code],
                )

        if remaining is not None:
            calories = float(item.get("calories", 0))
            if calories > float(remaining):
                return PartnerLineVerdict(
                    item_id, self._soft(strictness), CODE_CALORIES,
                    t(lang, CODE_CALORIES, calories=int(calories)),
                )

        return PartnerLineVerdict(item_id, "allow", CODE_OK, t(lang, CODE_OK))
