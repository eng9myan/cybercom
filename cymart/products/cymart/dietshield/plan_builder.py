"""Diet plan math — pure, testable, no LLM.

Mifflin-St Jeor BMR → TDEE → goal-adjusted target with a hard safety
floor → macro split. The LLM layer (added later) only writes the friendly
summary; the numbers come from here so they are correct and auditable.
"""

from __future__ import annotations

import datetime
from decimal import Decimal

from .models import ACTIVITY_FACTORS, DietPlan, DietProfile, GoalType, Sex

# 1 kg of body fat ≈ 7700 kcal.
KCAL_PER_KG = 7700
# Safe minimum daily intake floors (kcal) for a sustained deficit.
FLOOR_MALE = 1500
FLOOR_FEMALE = 1200
# Muscle-retention protein target (g per kg bodyweight) on a deficit.
PROTEIN_G_PER_KG = Decimal("1.8")
# Default keto net-carb ceiling (g/day) when no regime cap is set.
KETO_CARBS_G = 25


class PlanBuilder:
    def bmr(self, profile: DietProfile) -> float:
        """Mifflin-St Jeor resting metabolic rate."""
        w = float(profile.weight_kg)
        h = float(profile.height_cm)
        base = 10 * w + 6.25 * h - 5 * profile.age
        return base + (5 if profile.sex == Sex.MALE else -161)

    def tdee(self, profile: DietProfile) -> float:
        factor = ACTIVITY_FACTORS[profile.activity_level]
        return self.bmr(profile) * factor

    def safety_floor(self, profile: DietProfile) -> int:
        floor = FLOOR_MALE if profile.sex == Sex.MALE else FLOOR_FEMALE
        # Pregnancy / breastfeeding: never run a deficit — lift the floor to
        # maintenance so the target can't drop below upkeep.
        if profile.is_pregnant or profile.is_breastfeeding:
            return max(floor, int(round(self.tdee(profile))))
        return floor

    def target_calories(self, profile: DietProfile) -> tuple[int, int]:
        """Return (target_calories, safety_floor), target clamped to floor."""
        tdee = self.tdee(profile)
        daily_delta = float(profile.weekly_pace_kg) * KCAL_PER_KG / 7

        if profile.goal_type == GoalType.LOSE:
            target = tdee - daily_delta
        elif profile.goal_type == GoalType.GAIN:
            target = tdee + daily_delta
        else:
            target = tdee

        floor = self.safety_floor(profile)
        target = max(target, floor)
        return int(round(target)), floor

    def _is_keto(self, profile: DietProfile) -> tuple[bool, int]:
        for regime in profile.regimes.all():
            if regime.code == "keto" or regime.max_item_carbs_g is not None:
                cap = (
                    int(regime.max_item_carbs_g)
                    if regime.max_item_carbs_g is not None
                    else KETO_CARBS_G
                )
                return True, cap
        return False, 0

    def macros(self, profile: DietProfile, calories: int) -> tuple[int, int, int]:
        """Return (protein_g, carbs_g, fat_g) for the day's calorie target."""
        protein_g = round(float(profile.weight_kg) * float(PROTEIN_G_PER_KG))
        protein_kcal = protein_g * 4

        keto, carb_cap = self._is_keto(profile)
        if keto:
            carbs_g = carb_cap
            carbs_kcal = carbs_g * 4
            fat_kcal = max(calories - protein_kcal - carbs_kcal, 0)
            fat_g = round(fat_kcal / 9)
        else:
            remaining = max(calories - protein_kcal, 0)
            carbs_g = round((remaining * 0.55) / 4)
            fat_g = round((remaining * 0.45) / 9)
        return protein_g, carbs_g, fat_g

    def per_meal(self, calories: int) -> dict:
        return {
            "breakfast": round(calories * 0.25),
            "lunch": round(calories * 0.30),
            "dinner": round(calories * 0.30),
            "snack": round(calories * 0.15),
        }

    def build(self, profile: DietProfile, save: bool = True) -> DietPlan:
        bmr = int(round(self.bmr(profile)))
        tdee = int(round(self.tdee(profile)))
        calories, floor = self.target_calories(profile)
        protein_g, carbs_g, fat_g = self.macros(profile, calories)

        plan = DietPlan(
            profile=profile,
            bmr=bmr,
            tdee=tdee,
            daily_calories=calories,
            min_daily_calories=floor,
            protein_g=protein_g,
            carbs_g=carbs_g,
            fat_g=fat_g,
            per_meal=self.per_meal(calories),
            review_on=datetime.date.today() + datetime.timedelta(days=7),
        )
        if save:
            # Only one active plan per profile.
            DietPlan.objects.filter(profile=profile, is_active=True).update(
                is_active=False
            )
            plan.save()
        return plan
