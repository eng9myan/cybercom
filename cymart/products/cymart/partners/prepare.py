"""Kitchen instructions: once the customer has chosen an item, turn their plan
into the requirements the vendor must follow for THIS order, for example
"use gluten-free bread", "no tomato, no onion — customer allergy".

The engine never invents a change. A vendor lists, per item, the
modifications its kitchen can really make (``modifications``: remove an
ingredient, or substitute it from named options). Diet Shield picks which of
those are needed for this customer, applies them to a copy of the item,
re-checks the result with the same three gates as /evaluate/, and returns:

    instructions  structured, localisable, for the kitchen ticket
    vendor_note   the same, as plain text in English or Arabic
    verdict       the item re-checked AFTER the changes
    status        ok | ok_with_changes | needs_vendor_confirmation | cannot_make_safe

If an item cannot be made to fit with the modifications offered (or its
ingredients are unknown for an allergic customer) it says so; it never
reports an unfixable item as safe.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .allergens import Allergies, allergies_of
from .engine import PartnerShieldEngine, _tokens
from .i18n import join_list, normalise, t

STATUS_OK = "ok"
STATUS_CHANGED = "ok_with_changes"
STATUS_CONFIRM = "needs_vendor_confirmation"
STATUS_CANNOT = "cannot_make_safe"


@dataclass
class PrepareResult:
    item_id: str
    status: str
    verdict: dict
    instructions: list[dict] = field(default_factory=list)
    unresolved: list[dict] = field(default_factory=list)
    vendor_note: str = ""
    modified_item: dict = field(default_factory=dict)


def _norm(v) -> str:
    return normalise(v)


def _blocked_by_regime(regimes: list[dict], name: str, ingredients: list[str]) -> bool:
    toks = _tokens([name, *ingredients])
    return any(_tokens(r.get("block_ingredients")) & toks for r in regimes)


def _option_is_safe(opt: dict, allergies: Allergies, regimes: list[dict]) -> bool:
    parts = [opt.get("name", ""), *(opt.get("ingredients") or [])]
    if allergies and allergies.hits(_tokens(parts)):
        return False
    return not _blocked_by_regime(regimes, opt.get("name", ""), list(opt.get("ingredients") or []))


class KitchenInstructions:
    def __init__(self, lang: str = "en"):
        self.lang = lang if lang in ("en", "ar") else "en"
        self.engine = PartnerShieldEngine(self.lang)

    # -- applying one modification to a working copy of the item --------------
    @staticmethod
    def _apply(item: dict, mod: dict, option: dict | None):
        ingredients = [i for i in item["ingredients"] if _norm(i) != _norm(mod["ingredient"])]
        if option is not None:
            ingredients += [option["name"], *(option.get("ingredients") or [])]
        item["ingredients"] = ingredients
        opt = option or {}
        item["calories"] = float(item.get("calories", 0)) + float(mod.get("calories_delta") or 0) \
            + float(opt.get("calories_delta") or 0)
        item["carbs_g"] = float(item.get("carbs_g", 0)) + float(mod.get("carbs_g_delta") or 0) \
            + float(opt.get("carbs_g_delta") or 0)
        makes = list(item.get("diet_tags") or [])
        makes += list(mod.get("makes") or []) + list(opt.get("makes") or [])
        item["diet_tags"] = sorted(set(makes))

    def prepare(self, profile: dict, item: dict) -> PrepareResult:
        lang = self.lang
        allergies = allergies_of(profile.get("allergies"))
        regimes = profile.get("regimes") or []
        work = {
            **item,
            "ingredients": list(item.get("ingredients") or []),
            "diet_tags": list(item.get("diet_tags") or []),
        }
        mods = [m for m in item.get("modifications") or []]
        used: set[int] = set()
        instructions: list[dict] = []
        unresolved: list[dict] = []

        if allergies:
            names = list(allergies.names)
            instructions.append({
                "type": "allergy_alert", "priority": "critical", "allergens": names,
                "reason_code": "allergen_conflict",
                "text": t(lang, "alert_text", allergens=join_list(lang, names)),
                "_note": t(lang, "alert_note", allergens=join_list(lang, names)),
            })

        def modification_for(ingredient: str):
            for idx, m in enumerate(mods):
                if idx not in used and _norm(m["ingredient"]) == _norm(ingredient):
                    return idx, m
            return None, None

        def record(mod, option, code, why, priority, regime=None):
            if mod["action"] == "remove" or option is None:
                ins = {"type": "remove", "ingredient": mod["ingredient"]}
            else:
                ins = {"type": "substitute", "ingredient": mod["ingredient"], "replacement": option["name"]}
            ins.update({"priority": priority, "reason_code": code, "reason": why})
            if regime:
                ins["regime"] = regime
            instructions.append(ins)

        def choose_option(mod):
            if mod["action"] == "remove":
                return True, None
            for opt in mod.get("options") or []:
                if _option_is_safe(opt, allergies, regimes):
                    return True, opt
            return False, None

        # 1) Ingredients that conflict with an allergy or a diet rule.
        for ingredient in list(work["ingredients"]):
            tok = _norm(ingredient)
            allergen = allergies.hits({tok}) if allergies else []
            regime_codes = [str(r.get("code", "")).lower() for r in regimes
                            if tok in _tokens(r.get("block_ingredients"))]
            if not allergen and not regime_codes:
                continue
            code = "allergen_conflict" if allergen else "regime_blocked_ingredient"
            why = (t(lang, "why_allergy", ingredient=join_list(lang, allergen)) if allergen
                   else t(lang, "why_regime", regime=join_list(lang, regime_codes), ingredient=ingredient))
            idx, mod = modification_for(ingredient)
            ok, option = choose_option(mod) if mod else (False, None)
            if mod and ok:
                used.add(idx)
                self._apply(work, mod, option)
                record(mod, option, code, why, "critical" if allergen else "required",
                       regime_codes[0] if regime_codes else None)
            else:
                unresolved.append({"ingredient": ingredient, "reason_code": code, "reason": why})

        verdict = self.engine.check_item(profile, work)

        # 2) Still failing on carbs / diet tag / calories? Try the vendor's remaining
        #    modifications, in the order the vendor listed them, until it fits.
        for idx, mod in enumerate(mods):
            if verdict.severity == "allow":
                break
            if idx in used or _norm(mod["ingredient"]) not in {_norm(i) for i in work["ingredients"]}:
                continue
            helps = any(mod.get(k) for k in ("makes", "calories_delta", "carbs_g_delta")) or any(
                o.get("makes") or o.get("calories_delta") or o.get("carbs_g_delta")
                for o in mod.get("options") or [])
            if not helps:
                continue
            ok, option = choose_option(mod)
            if not ok:
                continue
            used.add(idx)
            self._apply(work, mod, option)
            record(mod, option, verdict.code, verdict.reason, "required")
            verdict = self.engine.check_item(profile, work)

        if verdict.code == "ingredients_unknown":
            status = STATUS_CONFIRM
            instructions.append({
                "type": "verify_ingredients", "priority": "critical", "reason_code": "ingredients_unknown",
                "text": t(lang, "verify_text"),
            })
        elif verdict.severity in ("block", "hard_block"):
            status = STATUS_CANNOT
        elif any(i["type"] in ("remove", "substitute") for i in instructions):
            status = STATUS_CHANGED
        else:
            status = STATUS_OK

        note = self._note(item, status, instructions, unresolved)
        for i in instructions:
            i.pop("_note", None)
        return PrepareResult(
            item_id=str(item.get("item_id", "")), status=status,
            verdict={"severity": verdict.severity, "code": verdict.code, "reason": verdict.reason},
            instructions=instructions, unresolved=unresolved, vendor_note=note,
            modified_item={
                "item_id": str(item.get("item_id", "")), "calories": work.get("calories", 0),
                "carbs_g": work.get("carbs_g", 0), "ingredients": work["ingredients"],
                "diet_tags": work["diet_tags"],
            },
        )

    def _note(self, item, status, instructions, unresolved) -> str:
        lang = self.lang
        lines = []
        for i in instructions:
            if i["type"] == "allergy_alert":
                lines.append(i["_note"])
            elif i["type"] == "remove":
                lines.append(t(lang, "note_remove", ingredient=i["ingredient"], reason=i["reason"]))
            elif i["type"] == "substitute":
                lines.append(t(lang, "note_substitute", replacement=i["replacement"],
                               ingredient=i["ingredient"], reason=i["reason"]))
            elif i["type"] == "verify_ingredients":
                lines.append(i["text"])
        for u in unresolved:
            lines.append(t(lang, "note_cannot", ingredient=u["ingredient"], reason=u["reason"]))
        header = t(lang, f"head_{status}", item=item.get("item_id", ""))
        return "\n".join([header, *lines])
