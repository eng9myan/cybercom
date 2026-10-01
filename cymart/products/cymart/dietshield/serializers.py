from rest_framework import serializers

from .models import DietPlan, DietProfile, DietRegime


class DietRegimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DietRegime
        fields = ["code", "name_en", "name_ar", "description_en", "max_item_carbs_g"]


class DietPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = DietPlan
        fields = [
            "id", "bmr", "tdee", "daily_calories", "min_daily_calories",
            "protein_g", "carbs_g", "fat_g", "per_meal", "valid_from",
            "review_on", "is_active",
        ]


class DietProfileSerializer(serializers.ModelSerializer):
    """customer_id is never accepted from the client — it comes from the
    verified JWT in the view. regime_codes is a write-only convenience that
    maps to the DietRegime M2M."""

    regime_codes = serializers.ListField(
        child=serializers.SlugField(), write_only=True, required=False
    )
    regimes = DietRegimeSerializer(many=True, read_only=True)

    class Meta:
        model = DietProfile
        fields = [
            "id", "sex", "age", "height_cm", "weight_kg", "activity_level",
            "goal_type", "target_weight_kg", "weekly_pace_kg", "strictness",
            "allergies", "medical_conditions", "is_pregnant", "is_breastfeeding",
            "regimes", "regime_codes", "is_active",
        ]
        read_only_fields = ["id", "regimes", "is_active"]

    def validate_age(self, v):
        if not (13 <= v <= 120):
            raise serializers.ValidationError("Age must be between 13 and 120.")
        return v

    def validate_weekly_pace_kg(self, v):
        if not (0 < v <= 1.0):
            raise serializers.ValidationError("Weekly pace must be > 0 and <= 1.0 kg.")
        return v


class EvaluateItemSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    quantity = serializers.DecimalField(max_digits=10, decimal_places=2, default=1)


class EvaluateRequestSerializer(serializers.Serializer):
    items = EvaluateItemSerializer(many=True)


class LineVerdictSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    severity = serializers.SerializerMethodField()
    gate = serializers.CharField()
    reason = serializers.CharField()
    allowed = serializers.BooleanField()
    swap_suggestion = serializers.UUIDField(allow_null=True)

    def get_severity(self, obj):
        return obj.severity.name
