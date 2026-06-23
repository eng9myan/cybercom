from rest_framework import serializers
from .models import Formulary, FormularyDrug, FormularyRestriction, TherapeuticClass, PreferredMedication


class TherapeuticClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = TherapeuticClass
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class FormularyRestrictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormularyRestriction
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class FormularyDrugSerializer(serializers.ModelSerializer):
    restrictions = FormularyRestrictionSerializer(many=True, read_only=True)
    therapeutic_class_name = serializers.CharField(source="therapeutic_class.name", read_only=True)

    class Meta:
        model = FormularyDrug
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class PreferredMedicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PreferredMedication
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class FormularySerializer(serializers.ModelSerializer):
    drugs = FormularyDrugSerializer(many=True, read_only=True)
    preferred_medications = PreferredMedicationSerializer(many=True, read_only=True)

    class Meta:
        model = Formulary
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
