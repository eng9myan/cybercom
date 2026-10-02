"""Weekly plan: fill every meal of the week from the platform's own items, with the shield applied.

The platform sends a pool of candidate items (its own menu, optionally tagged ``meal_types``). For each
meal slot the pool is judged as the kitchen could make it for this customer (only changes the
restaurant offers), checked against the slot's calorie budget, ranked by fit, and filled day by day with
variety. Only items that fully fit are ever planned; each slot also carries runners-up so the customer
can choose at meal time.

Deterministic and stateless: same input, same plan; the platform stores it.
"""

from __future__ import annotations

from collections import Counter

from ..i18n import t
from ..prepare import KitchenInstructions
from ..ranking import PartnerRanker

SLOTS = ("breakfast", "lunch", "dinner", "snack")
ALTERNATIVES = 2


def _public(item: dict, changes: list[dict], fit_score, summary: str) -> dict:
    return {
        "item_id": str(item["item_id"]), "name": item.get("name"), "restaurant": item.get("restaurant"),
        "price": item.get("price"), "calories": item.get("calories", 0), "fit_score": fit_score,
        "summary": summary, "changes": changes,
    }


def plan_week(shield_profile: dict, per_meal: dict, pool: list[dict], days: int = 7, slots=SLOTS,
              variety_window: int = 3, max_repeats: int = 2, lang: str = "en") -> dict:
    kitchen = KitchenInstructions(lang)
    prep_profile = {**shield_profile, "remaining_calories": None}

    candidates, changes_by_id, hidden = [], {}, Counter()
    for item in pool:
        k = kitchen.prepare(prep_profile, item)
        if k.status not in ("ok", "ok_with_changes"):
            hidden["ingredients_unknown" if k.status == "needs_vendor_confirmation" else k.verdict["code"]] += 1
            continue
        merged = {**item, **{f: k.modified_item[f] for f in ("calories", "carbs_g", "ingredients", "diet_tags")}}
        candidates.append(merged)
        ch = [{"type": i["type"], "ingredient": i["ingredient"], "replacement": i.get("replacement")}
              for i in k.instructions if i["type"] in ("remove", "substitute")]
        if ch:
            changes_by_id[str(item["item_id"])] = ch

    ranker = PartnerRanker(lang)
    by_id = {str(c["item_id"]): c for c in candidates}
    ordered: dict[str, list] = {}
    first_reason: dict[str, str] = {}
    for slot in slots:
        budget = per_meal.get(slot)
        if not budget:
            continue
        eligible = [c for c in candidates if not c.get("meal_types") or slot in c["meal_types"]]
        slot_profile = {**shield_profile, "remaining_calories": budget, "meal_calories_target": budget}
        if eligible:
            r = ranker.rank(slot_profile, eligible, limit=len(eligible), include_warnings=False)
            ordered[slot] = r.ranked
            for e in r.excluded:
                first_reason.setdefault(e["item_id"], e["code"])
        else:
            ordered[slot] = []

    used_total: Counter = Counter()
    recent: dict[str, list] = {s: [] for s in ordered}
    out_days, empty = [], 0
    for d in range(1, days + 1):
        day_slots, total, day_used = [], 0, set()
        for slot, ranked in ordered.items():
            budget = per_meal[slot]
            pick = None
            for strict in (True, False):                      # prefer variety; relax it rather than leave a slot empty
                for r in ranked:
                    if strict and (r.item_id in day_used or r.item_id in recent[slot][-variety_window:]
                                   or used_total[(slot, r.item_id)] >= max_repeats):
                        continue
                    pick = r
                    break
                if pick:
                    break
            if pick is None:
                empty += 1
                day_slots.append({"meal": slot, "budget_calories": budget, "item": None, "reason": "nothing_fits",
                                  "text": t(lang, "week_nothing_fits", meal=slot), "alternatives": []})
                continue
            recent[slot].append(pick.item_id)
            day_used.add(pick.item_id)
            used_total[(slot, pick.item_id)] += 1
            item = by_id[pick.item_id]
            total += float(item.get("calories") or 0)
            alts = [r for r in ranked if r.item_id != pick.item_id][:ALTERNATIVES]
            day_slots.append({
                "meal": slot, "budget_calories": budget,
                "item": _public(item, changes_by_id.get(pick.item_id, []), pick.fit_score, pick.summary),
                "alternatives": [_public(by_id[a.item_id], changes_by_id.get(a.item_id, []), a.fit_score, a.summary) for a in alts],
            })
        out_days.append({"day": d, "slots": day_slots, "total_calories": round(total),
                         "target_calories": sum(per_meal[s] for s in ordered)})

    filled = sum(1 for d in out_days for s in d["slots"] if s["item"])
    usable_ids = {r.item_id for ranked in ordered.values() for r in ranked}
    for cid in by_id:                       # passed the safety stage but fits no meal: say why, once
        if cid not in usable_ids:
            hidden[first_reason.get(cid, "no_matching_meal")] += 1
    return {
        "language": lang,
        "days": out_days,
        "summary": {
            "slots_total": filled + empty, "filled": filled, "empty": empty,
            "average_daily_calories": round(sum(d["total_calories"] for d in out_days) / max(len(out_days), 1)),
            "target_daily_calories": out_days[0]["target_calories"] if out_days else 0,
            "items_considered": len(pool), "items_usable": len(usable_ids),
            "hidden_by_plan": dict(hidden),
        },
        "notes": [t(lang, "week_note_choose")],
    }
