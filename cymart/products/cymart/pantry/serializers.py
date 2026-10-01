from rest_framework import serializers


class RecordPurchaseSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    quantity = serializers.DecimalField(max_digits=10, decimal_places=2)
    unit = serializers.CharField(max_length=20, required=False, allow_blank=True, default="")
    product_name = serializers.CharField(
        max_length=300, required=False, allow_blank=True, default=""
    )


class PantryItemSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    product_name = serializers.CharField(allow_blank=True)
    quantity = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)
    unit = serializers.CharField(allow_blank=True)
    predicted_runout_date = serializers.DateField(allow_null=True)


class ExplodeRecipesSerializer(serializers.Serializer):
    codes = serializers.ListField(child=serializers.SlugField(), min_length=1)
    servings_map = serializers.DictField(
        child=serializers.IntegerField(min_value=1), required=False
    )


class MatchedIngredientSerializer(serializers.Serializer):
    ingredient_name = serializers.CharField()
    product_id = serializers.UUIDField()
    product_name = serializers.CharField(allow_blank=True)
    quantity = serializers.DecimalField(max_digits=8, decimal_places=2)
    unit = serializers.CharField(allow_blank=True)


class UnmatchedIngredientSerializer(serializers.Serializer):
    ingredient_name = serializers.CharField()
    quantity = serializers.DecimalField(max_digits=8, decimal_places=2)
    unit = serializers.CharField(allow_blank=True)
