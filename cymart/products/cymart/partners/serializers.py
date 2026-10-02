from rest_framework import serializers


class RegimeDefSerializer(serializers.Serializer):
    code = serializers.CharField()
    block_ingredients = serializers.ListField(
        child=serializers.CharField(), required=False, default=list
    )
    max_item_carbs_g = serializers.FloatField(required=False, allow_null=True, default=None)


class PartnerProfileSerializer(serializers.Serializer):
    allergies = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    regimes = RegimeDefSerializer(many=True, required=False, default=list)
    remaining_calories = serializers.FloatField(required=False, allow_null=True, default=None)
    strictness = serializers.ChoiceField(
        choices=["strict", "balanced", "coach"], required=False, default="balanced"
    )


class PartnerAlternativeSerializer(serializers.Serializer):
    """A candidate replacement the partner's own catalog offers for an
    item — same shape as an item, but never nested further."""

    item_id = serializers.CharField()
    calories = serializers.FloatField(required=False, default=0)
    carbs_g = serializers.FloatField(required=False, default=0)
    ingredients = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    diet_tags = serializers.ListField(child=serializers.CharField(), required=False, default=list)


class PartnerItemSerializer(PartnerAlternativeSerializer):
    alternatives = PartnerAlternativeSerializer(many=True, required=False, default=list)

    def validate_alternatives(self, value):
        if len(value) > 5:
            raise serializers.ValidationError("At most 5 alternatives per item.")
        return value


LANGUAGE_CHOICES = ["en", "ar"]


class PartnerEvaluateRequestSerializer(serializers.Serializer):
    profile = PartnerProfileSerializer()
    # Language of the prose fields (reason). Codes never change.
    language = serializers.ChoiceField(choices=LANGUAGE_CHOICES, required=False, default="en")
    items = PartnerItemSerializer(many=True)
    # False: items are menu options, each checked on its own.
    # True: items are a cart, checked in order against a shrinking budget.
    cumulative = serializers.BooleanField(required=False, default=False)

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("At least one item is required.")
        if len(value) > 100:
            raise serializers.ValidationError("At most 100 items per call.")
        return value


class PartnerRankProfileSerializer(PartnerProfileSerializer):
    # Optional: how many kcal this meal should be. When sent, items closer
    # to it score higher. Otherwise calories do not affect the fit score.
    meal_calories_target = serializers.FloatField(
        required=False, allow_null=True, default=None, min_value=1
    )


class PartnerRankItemSerializer(PartnerAlternativeSerializer):
    # Optional: the partner's own relevance for this item (e.g. search score).
    # Only used to break ties between equally good fits.
    relevance = serializers.FloatField(required=False, allow_null=True, default=None)


class PartnerRankRequestSerializer(serializers.Serializer):
    profile = PartnerRankProfileSerializer()
    items = PartnerRankItemSerializer(many=True)
    language = serializers.ChoiceField(choices=LANGUAGE_CHOICES, required=False, default="en")
    limit = serializers.IntegerField(required=False, default=20, min_value=1, max_value=100)
    # False: only items that fully fit are returned; warnings are excluded.
    include_warnings = serializers.BooleanField(required=False, default=True)

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("At least one item is required.")
        if len(value) > 500:
            raise serializers.ValidationError("At most 500 items per call.")
        return value


class ModificationOptionSerializer(serializers.Serializer):
    """A replacement the vendor's kitchen can really make."""

    name = serializers.CharField()
    ingredients = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    makes = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    calories_delta = serializers.FloatField(required=False, default=0)
    carbs_g_delta = serializers.FloatField(required=False, default=0)


class ModificationSerializer(serializers.Serializer):
    """One change the vendor's kitchen offers for an item."""

    ingredient = serializers.CharField()
    action = serializers.ChoiceField(choices=["remove", "substitute"])
    options = ModificationOptionSerializer(many=True, required=False, default=list)
    makes = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    calories_delta = serializers.FloatField(required=False, default=0)
    carbs_g_delta = serializers.FloatField(required=False, default=0)

    def validate(self, attrs):
        if attrs["action"] == "substitute" and not attrs["options"]:
            raise serializers.ValidationError("A substitute modification needs at least one option.")
        return attrs


class PartnerPrepareItemSerializer(PartnerAlternativeSerializer):
    modifications = ModificationSerializer(many=True, required=False, default=list)

    def validate_modifications(self, value):
        if len(value) > 20:
            raise serializers.ValidationError("At most 20 modifications per item.")
        return value


class PartnerPrepareRequestSerializer(serializers.Serializer):
    profile = PartnerProfileSerializer()
    language = serializers.ChoiceField(choices=LANGUAGE_CHOICES, required=False, default="en")
    items = PartnerPrepareItemSerializer(many=True)

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("At least one item is required.")
        if len(value) > 50:
            raise serializers.ValidationError("At most 50 items per call.")
        return value
