"""CyMed Pharmacy Compounding serializers."""
from rest_framework import serializers

from .models import (
    CompoundingFormulation,
    CompoundingIngredient,
    CompoundingOrder,
    CompoundingStep,
    IngredientLot,
    QATest,
)


class CompoundingFormulationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompoundingFormulation
        fields = "__all__"


class CompoundingIngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompoundingIngredient
        fields = "__all__"


class CompoundingOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompoundingOrder
        fields = "__all__"


class CompoundingStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompoundingStep
        fields = "__all__"


class IngredientLotSerializer(serializers.ModelSerializer):
    class Meta:
        model = IngredientLot
        fields = "__all__"


class QATestSerializer(serializers.ModelSerializer):
    class Meta:
        model = QATest
        fields = "__all__"
