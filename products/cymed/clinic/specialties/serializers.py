from rest_framework import serializers
from products.cymed.clinic.specialties.models import SpecialtyProfile, SpecialtyTemplate, SpecialtyQuestionnaire, SpecialtyClinicalRule

class SpecialtyProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpecialtyProfile
        fields = "__all__"

    def create(self, validated_data):
        request = self.context.get("request")
        if request and hasattr(request, "tenant_id"):
            validated_data["tenant_id"] = request.tenant_id
        return super().create(validated_data)

class SpecialtyTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpecialtyTemplate
        fields = "__all__"

    def create(self, validated_data):
        request = self.context.get("request")
        if request and hasattr(request, "tenant_id"):
            validated_data["tenant_id"] = request.tenant_id
        return super().create(validated_data)

class SpecialtyQuestionnaireSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpecialtyQuestionnaire
        fields = "__all__"

    def create(self, validated_data):
        request = self.context.get("request")
        if request and hasattr(request, "tenant_id"):
            validated_data["tenant_id"] = request.tenant_id
        return super().create(validated_data)

class SpecialtyClinicalRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpecialtyClinicalRule
        fields = "__all__"

    def create(self, validated_data):
        request = self.context.get("request")
        if request and hasattr(request, "tenant_id"):
            validated_data["tenant_id"] = request.tenant_id
        return super().create(validated_data)
