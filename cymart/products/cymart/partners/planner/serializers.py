from rest_framework import serializers

from ..serializers import LANGUAGE_CHOICES, PartnerPrepareItemSerializer, PartnerRankProfileSerializer

MEALS = ["breakfast", "lunch", "dinner", "snack"]


class IntakeSerializer(serializers.Serializer):
    sex = serializers.ChoiceField(choices=["male", "female"])
    age = serializers.IntegerField(min_value=1, max_value=110)
    height_cm = serializers.FloatField(min_value=120, max_value=230)
    weight_kg = serializers.FloatField(min_value=35, max_value=250)
    activity = serializers.ChoiceField(choices=["sedentary", "light", "moderate", "active", "very_active"], required=False, default="sedentary")
    goal = serializers.ChoiceField(choices=["lose", "maintain", "gain"], required=False, default="maintain")
    weekly_pace_kg = serializers.FloatField(min_value=0.1, max_value=1.0, required=False, default=0.5)
    pregnant = serializers.BooleanField(required=False, default=False)
    breastfeeding = serializers.BooleanField(required=False, default=False)
    medical_conditions = serializers.BooleanField(required=False, default=False)
    allergies = serializers.ListField(child=serializers.CharField(), required=False, default=list, max_length=30)
    regimes = serializers.ListField(child=serializers.CharField(max_length=40), required=False, default=list, max_length=6)
    strictness = serializers.ChoiceField(choices=["strict", "balanced", "coach"], required=False, default="balanced")

    def validate_age(self, value):
        if value < 18:
            raise serializers.ValidationError("Plans are for adults. For anyone under 18, please ask a doctor or dietitian.")
        return value


class TargetsRequestSerializer(serializers.Serializer):
    language = serializers.ChoiceField(choices=LANGUAGE_CHOICES, required=False, default="en")
    intake = IntakeSerializer()


class PoolItemSerializer(PartnerPrepareItemSerializer):
    name = serializers.CharField(required=False, allow_blank=True)
    restaurant = serializers.CharField(required=False, allow_blank=True)
    price = serializers.FloatField(required=False, allow_null=True)
    meal_types = serializers.ListField(child=serializers.ChoiceField(choices=MEALS), required=False, default=list)
    category = serializers.CharField(required=False, allow_blank=True)
    servings = serializers.IntegerField(required=False, default=1, min_value=1, max_value=50)


def _pool_validator(value):
    if not value:
        raise serializers.ValidationError("At least one item is required.")
    if len(value) > 300:
        raise serializers.ValidationError("At most 300 items per call.")
    return value


class WeekRequestSerializer(serializers.Serializer):
    language = serializers.ChoiceField(choices=LANGUAGE_CHOICES, required=False, default="en")
    shield_profile = PartnerRankProfileSerializer()
    per_meal = serializers.DictField(child=serializers.FloatField(min_value=50, max_value=3000))
    pool = PoolItemSerializer(many=True)
    days = serializers.IntegerField(min_value=1, max_value=14, required=False, default=7)
    slots = serializers.ListField(child=serializers.ChoiceField(choices=MEALS), required=False, default=lambda: list(MEALS))

    def validate_pool(self, value):
        return _pool_validator(value)

    def validate_per_meal(self, value):
        bad = set(value) - set(MEALS)
        if bad:
            raise serializers.ValidationError(f"Unknown meal(s): {', '.join(sorted(bad))}.")
        return value


class BasketRequestSerializer(serializers.Serializer):
    language = serializers.ChoiceField(choices=LANGUAGE_CHOICES, required=False, default="en")
    shield_profile = PartnerRankProfileSerializer()
    weekly_calories = serializers.FloatField(min_value=500, max_value=60000)
    pool = PoolItemSerializer(many=True)
    needs = serializers.DictField(child=serializers.IntegerField(min_value=0, max_value=70), required=False, default=dict)

    def validate_pool(self, value):
        return _pool_validator(value)
