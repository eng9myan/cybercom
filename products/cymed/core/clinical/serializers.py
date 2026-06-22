from rest_framework import serializers
from products.cymed.core.clinical.models import Condition, Allergy, AllergyReaction, VitalSign, Observation, ClinicalFlag
from platform.terminology.services import TerminologyService

class ConditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Condition
        fields = [
            "id", "patient", "encounter", "code", "display", "system",
            "clinical_status", "verification_status", "onset_date", "recorded_at", "recorded_by"
        ]
        read_only_fields = ["recorded_at"]

    def validate(self, attrs):
        system = attrs.get("system")  # "icd11" or "snomed"
        code = attrs.get("code")
        request = self.context.get("request")
        
        tenant_id = getattr(request, "tenant_id", "00000000-0000-0000-0000-000000000000")
        requested_by = str(request.user) if request else "system"

        # Validate code using TerminologyService
        try:
            is_valid = TerminologyService.validate(
                provider=system,
                code=code,
                tenant_id=str(tenant_id),
                requested_by=requested_by
            )
        except Exception:
            # Fallback if terminology app is not active or errors
            is_valid = False

        if not is_valid:
            raise serializers.ValidationError({
                "code": f"Diagnosis code '{code}' is not valid in system '{system}'."
            })

        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        if request and hasattr(request, "tenant_id"):
            validated_data["tenant_id"] = request.tenant_id

        return super().create(validated_data)


class AllergyReactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AllergyReaction
        fields = ["id", "manifestation_code", "severity"]

class AllergySerializer(serializers.ModelSerializer):
    reactions = AllergyReactionSerializer(many=True, required=False)

    class Meta:
        model = Allergy
        fields = ["id", "patient", "category", "substance_code", "substance_display", "clinical_status", "reactions", "recorded_at"]

    def create(self, validated_data):
        reactions_data = validated_data.pop("reactions", [])
        request = self.context.get("request")
        if request and hasattr(request, "tenant_id"):
            validated_data["tenant_id"] = request.tenant_id

        allergy = Allergy.objects.create(**validated_data)
        for rx in reactions_data:
            AllergyReaction.objects.create(allergy=allergy, tenant_id=allergy.tenant_id, **rx)
        return allergy


class VitalSignSerializer(serializers.ModelSerializer):
    class Meta:
        model = VitalSign
        fields = ["id", "patient", "encounter", "taken_at", "taken_by", "type", "value", "unit"]

    def create(self, validated_data):
        request = self.context.get("request")
        if request and hasattr(request, "tenant_id"):
            validated_data["tenant_id"] = request.tenant_id
        return super().create(validated_data)


class ObservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Observation
        fields = ["id", "patient", "encounter", "code", "display", "value_quantity", "value_string", "unit", "reference_range", "status"]

    def create(self, validated_data):
        request = self.context.get("request")
        if request and hasattr(request, "tenant_id"):
            validated_data["tenant_id"] = request.tenant_id
        return super().create(validated_data)


class ClinicalFlagSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClinicalFlag
        fields = ["id", "patient", "flag_text", "category", "status"]
