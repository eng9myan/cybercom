import uuid
from decimal import Decimal

import pytest

from products.cymart.dietshield.models import (
    ActivityLevel,
    DietProfile,
    DietRegime,
    GoalType,
    Sex,
)
from products.cymart.dietshield.plan_builder import PlanBuilder


def _profile(**kw):
    defaults = dict(
        customer_id=uuid.uuid4(),
        sex=Sex.MALE,
        age=34,
        height_cm=Decimal("178"),
        weight_kg=Decimal("92"),
        activity_level=ActivityLevel.SEDENTARY,
        goal_type=GoalType.LOSE,
        weekly_pace_kg=Decimal("0.5"),
    )
    defaults.update(kw)
    return DietProfile.objects.create(**defaults)


@pytest.mark.django_db
class TestPlanBuilder:
    def test_mifflin_st_jeor_male_reference(self):
        # 10*92 + 6.25*178 - 5*34 + 5 = 1867.5
        assert round(PlanBuilder().bmr(_profile())) == 1868

    def test_mifflin_st_jeor_female_reference(self):
        p = _profile(sex=Sex.FEMALE, weight_kg=Decimal("60"), height_cm=Decimal("165"), age=30)
        # 10*60 + 6.25*165 - 5*30 - 161 = 1320.25
        assert round(PlanBuilder().bmr(p)) == 1320

    def test_lose_goal_applies_deficit(self):
        plan = PlanBuilder().build(_profile())
        assert plan.daily_calories < plan.tdee

    def test_never_below_female_floor(self):
        p = _profile(sex=Sex.FEMALE, weight_kg=Decimal("52"), height_cm=Decimal("158"),
                     age=30, weekly_pace_kg=Decimal("1.0"))
        assert PlanBuilder().build(p).daily_calories >= 1200

    def test_pregnancy_prevents_deficit(self):
        p = _profile(sex=Sex.FEMALE, is_pregnant=True)
        plan = PlanBuilder().build(p)
        assert plan.daily_calories >= plan.tdee

    def test_keto_regime_caps_carbs(self):
        p = _profile(goal_type=GoalType.MAINTAIN)
        keto, _ = DietRegime.objects.get_or_create(
            code="keto",
            defaults={"name_en": "Keto", "max_item_carbs_g": Decimal("15")},
        )
        p.regimes.add(keto)
        assert PlanBuilder().build(p).carbs_g <= 15

    def test_only_one_active_plan(self):
        p = _profile()
        pb = PlanBuilder()
        pb.build(p)
        pb.build(p)
        assert p.plans.filter(is_active=True).count() == 1
