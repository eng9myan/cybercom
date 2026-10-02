"""Weekly grocery basket: shield-checked staples for the plan, from the platform's own grocery items.

For each food group the plan needs (a starter template the platform can override with `needs`), the best
fully-fitting item is chosen and the number of packs worked out; runners-up are returned so the customer
can swap. The finished basket is then re-checked as one basket against the week's calorie budget.

Grocery items are shielded exactly like meals: packaged-food ingredient lists drive the allergy check, and an
item with no ingredient list is reported "unverified" for an allergic customer, never safe. Fresh produce with no
declared ingredients is the platform's data decision: send the item's own name as its single ingredient.
"""

from __future__ import annotations

import math
from collections import Counter

from ..engine import PartnerShieldEngine
from ..i18n import t
from ..ranking import PartnerRanker
from .packs import DEFAULT_WEEKLY_SERVINGS, REGIME_WEEKLY_OVERRIDES

ALTERNATIVES = 2


def weekly_needs(shield_profile: dict, override: dict | None = None) -> dict[str, int]:
    needs = dict(DEFAULT_WEEKLY_SERVINGS)
    for r in shield_profile.get("regimes") or []:
        needs.update(REGIME_WEEKLY_OVERRIDES.get(str(r.get("code", "")).lower(), {}))
    if override:
        needs.update({k: int(v) for k, v in override.items()})
    return {k: v for k, v in needs.items() if v > 0}


def build_basket(shield_profile: dict, pool: list[dict], weekly_calories: float, needs: dict | None = None, lang: str = "en") -> dict:
    wanted = weekly_needs(shield_profile, needs)
    profile = {**shield_profile, "remaining_calories": weekly_calories}
    ranker, engine = PartnerRanker(lang), PartnerShieldEngine(lang)
    hidden: Counter = Counter()
    lines, gaps = [], []

    for category, servings in wanted.items():
        group = [i for i in pool if str(i.get("category", "")).lower() == category]
        if not group:
            gaps.append({"category": category, "reason": "no_items", "text": t(lang, "basket_no_items", category=category)})
            continue
        r = ranker.rank(profile, group, limit=len(group), include_warnings=False)
        for e in r.excluded:
            hidden[e["code"]] += 1
        if not r.ranked:
            gaps.append({"category": category, "reason": "nothing_fits", "text": t(lang, "basket_nothing_fits", category=category)})
            continue
        by_id = {str(i["item_id"]): i for i in group}
        best = r.ranked[0]
        item = by_id[best.item_id]
        per_pack = max(1, int(item.get("servings") or 1))
        packs = math.ceil(servings / per_pack)
        lines.append({
            "category": category, "item_id": best.item_id, "name": item.get("name"), "price": item.get("price"),
            "packs": packs, "servings": packs * per_pack, "servings_needed": servings,
            "calories": round(float(item.get("calories") or 0) * packs), "fit_score": best.fit_score, "summary": best.summary,
            "alternatives": [{"item_id": a.item_id, "name": by_id[a.item_id].get("name"), "summary": a.summary} for a in r.ranked[1:1 + ALTERNATIVES]],
        })

    # the basket as one basket, against the week's budget
    scaled = [{"item_id": l["item_id"], "calories": l["calories"], "carbs_g": 0,
               **{k: v for k, v in next(i for i in pool if str(i["item_id"]) == l["item_id"]).items() if k in ("ingredients", "diet_tags")}}
              for l in lines]
    verdict = engine.evaluate(profile, scaled, cumulative=True) if scaled else None
    over = [ln.item_id for ln in verdict.lines if ln.severity != "allow"] if verdict else []
    total = sum(l["calories"] for l in lines)
    return {
        "language": lang, "lines": lines, "gaps": gaps,
        "totals": {"calories": total, "weekly_budget": round(weekly_calories),
                   "within_budget": not over, "over_budget_items": over},
        "hidden_by_plan": dict(hidden),
        "needs": wanted,
        "notes": [t(lang, "basket_note_template")],
    }
