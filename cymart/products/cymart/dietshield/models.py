import uuid

from django.db import models


class Sex(models.TextChoices):
    MALE = "male", "Male"
    FEMALE = "female", "Female"


class ActivityLevel(models.TextChoices):
    """Standard TDEE activity multipliers (Mifflin-St Jeor)."""

    SEDENTARY = "sedentary", "Sedentary"
    LIGHT = "light", "Lightly active"
    MODERATE = "moderate", "Moderately active"
    ACTIVE = "active", "Very active"
    ATHLETE = "athlete", "Extra active"


ACTIVITY_FACTORS = {
    ActivityLevel.SEDENTARY: 1.2,
    ActivityLevel.LIGHT: 1.375,
    ActivityLevel.MODERATE: 1.55,
    ActivityLevel.ACTIVE: 1.725,
    ActivityLevel.ATHLETE: 1.9,
}


class GoalType(models.TextChoices):
    LOSE = "lose", "Lose weight"
    MAINTAIN = "maintain", "Maintain"
    GAIN = "gain", "Gain / build"


class Strictness(models.TextChoices):
    """How hard the shield enforces the quantity/regime gates. Safety
    (allergy/medical) is always a hard block regardless of this."""

    STRICT = "strict", "Strict — block off-plan"
    BALANCED = "balanced", "Balanced — warn, allow override"
    COACH = "coach", "Coach — advise only"


class NutritionSource(models.TextChoices):
    MERCHANT = "merchant", "Merchant-entered"
    ESTIMATED = "estimated", "AI-estimated"
    VERIFIED = "verified", "Lab / verified"


class DietRegime(models.Model):
    """A data-driven diet rule pack (keto, gluten-free, vegan, halal…).

    Composition rules, evaluated by the RegimeGate. Kept as data (a row)
    rather than code so new diets are added without a deploy. An item
    passes a regime when its NutritionFact carries the regime's ``code``
    in ``diet_tags`` and violates none of the ingredient/macro rules
    below.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.SlugField(max_length=40, unique=True)
    name_en = models.CharField(max_length=120)
    name_ar = models.CharField(max_length=120, blank=True)
    description_en = models.CharField(max_length=300, blank=True)

    # Ingredient names (lowercased) that disqualify any item containing them.
    block_ingredients = models.JSONField(default=list, blank=True)
    # Per-item hard cap on net carbs (e.g. keto). Null = no cap.
    max_item_carbs_g = models.DecimalField(
        max_digits=6, decimal_places=1, null=True, blank=True
    )
    # If True the regime is a hard requirement (block); if False, advisory.
    is_hard = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cymart_diet_regime"
        ordering = ["name_en"]

    def __str__(self):
        return self.name_en


class DietProfile(models.Model):
    """A customer's body, goal, regimes and safety constraints. Its mere
    existence turns the shield on for that customer; without one, ordering
    is unguarded (a plain delivery app)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer_id = models.UUIDField(unique=True, db_index=True)

    sex = models.CharField(max_length=6, choices=Sex.choices)
    age = models.PositiveSmallIntegerField()
    height_cm = models.DecimalField(max_digits=5, decimal_places=1)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=1)
    activity_level = models.CharField(
        max_length=12, choices=ActivityLevel.choices, default=ActivityLevel.SEDENTARY
    )

    goal_type = models.CharField(max_length=8, choices=GoalType.choices)
    target_weight_kg = models.DecimalField(
        max_digits=5, decimal_places=1, null=True, blank=True
    )
    # Desired kg change per week (0.25–1.0 typical). Drives the deficit.
    weekly_pace_kg = models.DecimalField(max_digits=3, decimal_places=2, default=0.5)

    strictness = models.CharField(
        max_length=8, choices=Strictness.choices, default=Strictness.BALANCED
    )
    regimes = models.ManyToManyField(DietRegime, blank=True, related_name="profiles")

    # Free-text lowercased tokens matched against item allergens/ingredients.
    allergies = models.JSONField(default=list, blank=True)
    medical_conditions = models.JSONField(default=list, blank=True)
    is_pregnant = models.BooleanField(default=False)
    is_breastfeeding = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cymart_diet_profile"

    def __str__(self):
        return f"DietProfile({self.customer_id}, {self.goal_type})"


class DietPlan(models.Model):
    """A computed daily calorie/macro target for a profile. Regenerated
    when the profile changes or on a weekly review."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(
        DietProfile, on_delete=models.CASCADE, related_name="plans"
    )

    bmr = models.PositiveIntegerField()
    tdee = models.PositiveIntegerField()
    daily_calories = models.PositiveIntegerField()
    # Hard safety floor — the shield never lets a day drop below this.
    min_daily_calories = models.PositiveIntegerField()

    protein_g = models.PositiveIntegerField()
    carbs_g = models.PositiveIntegerField()
    fat_g = models.PositiveIntegerField()

    # {"breakfast": 400, "lunch": 500, "dinner": 500, "snack": 200}
    per_meal = models.JSONField(default=dict, blank=True)

    is_active = models.BooleanField(default=True)
    valid_from = models.DateField(auto_now_add=True)
    review_on = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cymart_diet_plan"
        ordering = ["-created_at"]

    def __str__(self):
        return f"DietPlan({self.daily_calories}kcal)"


class NutritionFact(models.Model):
    """Per-product nutrition + diet tags, keyed by the external product_id
    (products live in CyShop/CyCom services, referenced by UUID). Populated
    by merchant entry, verified data, or AI estimation. This cache is what
    every shield gate reads — the app is only as good as this data."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product_id = models.UUIDField(unique=True, db_index=True)
    name_snapshot = models.CharField(max_length=300, blank=True)

    serving_desc = models.CharField(max_length=120, blank=True)
    calories = models.DecimalField(max_digits=8, decimal_places=1, default=0)
    protein_g = models.DecimalField(max_digits=7, decimal_places=1, default=0)
    carbs_g = models.DecimalField(max_digits=7, decimal_places=1, default=0)
    fat_g = models.DecimalField(max_digits=7, decimal_places=1, default=0)
    sodium_mg = models.DecimalField(max_digits=8, decimal_places=1, default=0)
    sugar_g = models.DecimalField(max_digits=7, decimal_places=1, default=0)

    # Lowercased ingredient tokens, e.g. ["wheat", "chicken", "olive oil"].
    ingredients = models.JSONField(default=list, blank=True)
    # Regime codes this item is compatible with, e.g. ["keto", "gluten_free"].
    diet_tags = models.JSONField(default=list, blank=True)
    # Allergen tokens present, e.g. ["peanut", "shellfish", "gluten"].
    contains_allergens = models.JSONField(default=list, blank=True)

    source = models.CharField(
        max_length=10, choices=NutritionSource.choices, default=NutritionSource.MERCHANT
    )
    # 0.0–1.0 — low for AI estimates, high for verified data.
    confidence = models.DecimalField(max_digits=3, decimal_places=2, default=1.0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cymart_nutrition_fact"

    def __str__(self):
        return f"NutritionFact({self.name_snapshot or self.product_id})"


class DietDay(models.Model):
    """A running daily consumption log for a profile — what the quantity
    gate subtracts from the plan's daily budget."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(
        DietProfile, on_delete=models.CASCADE, related_name="days"
    )
    date = models.DateField()

    consumed_calories = models.DecimalField(max_digits=9, decimal_places=1, default=0)
    consumed_protein_g = models.DecimalField(max_digits=8, decimal_places=1, default=0)
    consumed_carbs_g = models.DecimalField(max_digits=8, decimal_places=1, default=0)
    consumed_fat_g = models.DecimalField(max_digits=8, decimal_places=1, default=0)
    off_plan_overrides = models.PositiveIntegerField(default=0)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cymart_diet_day"
        constraints = [
            models.UniqueConstraint(fields=["profile", "date"], name="unique_profile_day")
        ]

    def __str__(self):
        return f"DietDay({self.date}, {self.consumed_calories}kcal)"
