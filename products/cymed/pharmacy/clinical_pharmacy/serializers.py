from rest_framework import serializers
from .models import MedicationReview, ClinicalIntervention, PharmacistRecommendation, MedicationTherapyManagement


class ClinicalInterventionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClinicalIntervention
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at", "intervened_at"]


class PharmacistRecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PharmacistRecommendation
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class MedicationReviewSerializer(serializers.ModelSerializer):
    interventions = ClinicalInterventionSerializer(many=True, read_only=True)
    recommendations = PharmacistRecommendationSerializer(many=True, read_only=True)

    class Meta:
        model = MedicationReview
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class MedicationTherapyManagementSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicationTherapyManagement
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
