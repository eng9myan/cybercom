"""Plan setup: from a person's details to daily calorie and macro targets and a shield profile.

Pure arithmetic, no AI and no stored data: Mifflin-St Jeor resting rate -> activity -> goal, with a hard
safety floor, a cap on the pace of weight change, and no deficit during pregnancy or breastfeeding.
The assistant can explain and act on the result; the numbers always come from here so they can be audited.

This is a starting plan, not medical advice. A condition that affects diet (diabetes, kidney disease,
an eating disorder and so on) is flagged for professional review rather than handled here.
"""

from __future__ import annotations

from ..i18n import t
from .packs import MEAL_SPLIT, regime_rule

ACTIVITY = {"sedentary": 1.2, "light": 1.375, "moderate": 1.55, "active": 1.725, "very_active": 1.9}
FLOOR = {"male": 1500, "female": 1200}
KCAL_PER_KG = 7700
PROTEIN_G_PER_KG = {"lose": 1.8, "maintain": 1.4, "gain": 1.6}
KETO_DAILY_CARBS_G = 25
MAX_PACE_FRACTION = 0.01  # at most 1% of body weight per week


def bmr(sex: str, age: int, height_cm: float, weight_kg: float) -> float:
    return 10 * weight_kg + 6.25 * height_cm - 5 * age + (5 if sex == "male" else -161)


def build_targets(intake: dict, lang: str = "en") -> dict:
    sex, age = intake["sex"], int(intake["age"])
    height, weight = float(intake["height_cm"]), float(intake["weight_kg"])
    goal = intake.get("goal", "maintain")
    carers = bool(intake.get("pregnant") or intake.get("breastfeeding"))
    warnings: list[dict] = []

    base = bmr(sex, age, height, weight)
    tdee = base * ACTIVITY[intake.get("activity", "sedentary")]

    pace = float(intake.get("weekly_pace_kg") or 0.5)
    cap = round(weight * MAX_PACE_FRACTION, 2)
    if pace > cap:
        warnings.append({"code": "pace_capped", "text": t(lang, "plan_pace_capped", pace=f"{pace:g}", cap=f"{cap:g}")})
        pace = cap
    delta = pace * KCAL_PER_KG / 7

    floor = FLOOR[sex]
    if carers:
        floor = max(floor, round(tdee))
        warnings.append({"code": "no_deficit", "text": t(lang, "plan_no_deficit")})
        if goal == "lose":
            goal = "maintain"
    target = tdee - delta if goal == "lose" else tdee + delta if goal == "gain" else tdee
    if target < floor:
        warnings.append({"code": "floor_applied", "text": t(lang, "plan_floor", floor=floor)})
        target = floor
    calories = int(round(target))

    if intake.get("medical_conditions"):
        warnings.append({"code": "professional_review", "text": t(lang, "plan_medical")})

    protein_g = round(weight * PROTEIN_G_PER_KG[goal])
    codes = [str(r).lower() for r in intake.get("regimes") or []]
    keto = "keto" in codes
    if keto:
        carbs_g = KETO_DAILY_CARBS_G
        fat_g = round(max(calories - protein_g * 4 - carbs_g * 4, 0) / 9)
    else:
        rest = max(calories - protein_g * 4, 0)
        carbs_g, fat_g = round(rest * 0.55 / 4), round(rest * 0.45 / 9)

    per_meal = {m: round(calories * f) for m, f in MEAL_SPLIT.items()}
    return {
        "language": lang,
        "goal": goal,
        "bmr": round(base),
        "tdee": round(tdee),
        "daily_calories": calories,
        "safety_floor": floor,
        "weekly_pace_kg": pace,
        "protein_g": protein_g,
        "carbs_g": carbs_g,
        "fat_g": fat_g,
        "per_meal": per_meal,
        "review_in_days": 7,
        "warnings": warnings,
        "disclaimer": t(lang, "plan_disclaimer"),
        # ready to pass to /evaluate/, /rank/, /agent/turn/ as `profile`
        "shield_profile": {
            "allergies": list(intake.get("allergies") or []),
            "regimes": [regime_rule(c, carbs_g if keto else None) for c in codes],
            "remaining_calories": calories,
            "strictness": intake.get("strictness", "balanced"),
        },
    }
