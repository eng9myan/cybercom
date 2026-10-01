import datetime
import uuid
from decimal import Decimal

import pytest

from products.cymart.dietshield.models import (
    ActivityLevel,
    DietDay,
    DietProfile,
    DietRegime,
    GoalType,
    NutritionFact,
    Sex,
    Strictness,
)
from products.cymart.dietshield.plan_builder import PlanBuilder
from products.cymart.dietshield.shield import DietShield, Severity


def _profile(**kw):
    defaults = dict(
        customer_id=uuid.uuid4(), sex=Sex.MALE, age=40, height_cm=Decimal("180"),
        weight_kg=Decimal("90"), activity_level=ActivityLevel.MODERATE,
        goal_type=GoalType.MAINTAIN, strictness=Strictness.STRICT,
    )
    defaults.update(kw)
    return DietProfile.objects.create(**defaults)


def _fact(**kw):
    defaults = dict(product_id=uuid.uuid4(), calories=Decimal("400"), carbs_g=Decimal("10"))
    defaults.update(kw)
    return NutritionFact.objects.create(**defaults)


@pytest.mark.django_db
class TestDietShield:
    def setup_method(self):
        self.shield = DietShield()
        self.pb = PlanBuilder()

    def test_compliant_item_allowed(self):
        p = _profile()
        keto, _ = DietRegime.objects.get_or_create(
            code="keto", defaults={"name_en": "Keto", "max_item_carbs_g": Decimal("15")})
        p.regimes.add(keto)
        plan = self.pb.build(p)
        f = _fact(diet_tags=["keto"], carbs_g=Decimal("6"), calories=Decimal("480"))
        r = self.shield.evaluate(p, plan, None, [{"product_id": f.product_id, "quantity": Decimal("1")}])
        assert r.overall == Severity.ALLOW and r.allowed

    def test_regime_violation_blocks_in_strict(self):
        p = _profile()
        keto, _ = DietRegime.objects.get_or_create(
            code="keto", defaults={"name_en": "Keto", "max_item_carbs_g": Decimal("15")})
        p.regimes.add(keto)
        plan = self.pb.build(p)
        f = _fact(diet_tags=[], carbs_g=Decimal("82"), calories=Decimal("820"))
        r = self.shield.evaluate(p, plan, None, [{"product_id": f.product_id, "quantity": Decimal("1")}])
        assert r.overall == Severity.BLOCK
        assert r.lines[0].gate == "regime"

    def test_allergy_is_hard_block_even_in_coach(self):
        p = _profile(strictness=Strictness.COACH, allergies=["peanut"])
        plan = self.pb.build(p)
        f = _fact(contains_allergens=["peanut"])
        r = self.shield.evaluate(p, plan, None, [{"product_id": f.product_id, "quantity": Decimal("1")}])
        assert r.overall == Severity.HARD_BLOCK

    def test_over_budget_warns_in_coach(self):
        p = _profile(strictness=Strictness.COACH)
        plan = self.pb.build(p)
        day = DietDay.objects.create(profile=p, date=datetime.date.today(),
                                     consumed_calories=Decimal(str(plan.daily_calories - 100)))
        f = _fact(calories=Decimal("600"))
        r = self.shield.evaluate(p, plan, day, [{"product_id": f.product_id, "quantity": Decimal("1")}])
        assert r.overall == Severity.WARN and r.lines[0].gate == "quantity"

    def test_unknown_nutrition_blocks_strict_with_rules(self):
        p = _profile(allergies=["peanut"])
        plan = self.pb.build(p)
        r = self.shield.evaluate(p, plan, None, [{"product_id": uuid.uuid4(), "quantity": Decimal("1")}])
        assert r.overall == Severity.BLOCK
        assert r.lines[0].gate == "unknown"

    def test_hypertension_high_sodium_flagged(self):
        p = _profile(strictness=Strictness.BALANCED, medical_conditions=["hypertension"])
        plan = self.pb.build(p)
        f = _fact(sodium_mg=Decimal("1500"))
        r = self.shield.evaluate(p, plan, None, [{"product_id": f.product_id, "quantity": Decimal("1")}])
        assert r.overall == Severity.WARN and r.lines[0].gate == "safety"
