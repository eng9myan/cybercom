import random
from rest_framework import serializers
from products.cymed.clinic.insurance_bridge.models import Payer, InsurancePlan, EligibilityCheck, AuthorizationRequest, AuthorizationResponse

class PayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payer
        fields = "__all__"

class InsurancePlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = InsurancePlan
        fields = "__all__"

class EligibilityCheckSerializer(serializers.ModelSerializer):
    class Meta:
        model = EligibilityCheck
        fields = ["id", "patient", "plan", "checked_at", "is_eligible", "response_details"]
        read_only_fields = ["checked_at", "is_eligible", "response_details"]

    def create(self, validated_data):
        request = self.context.get("request")
        tenant_id = getattr(request, "tenant_id", "00000000-0000-0000-0000-000000000000")
        validated_data["tenant_id"] = tenant_id

        # Mock Eligibility Validation
        is_eligible = True
        response_details = {
            "card_status": "active",
            "coverage_valid": True,
            "copay_percent": float(validated_data["plan"].copay_percentage)
        }

        return EligibilityCheck.objects.create(
            is_eligible=is_eligible,
            response_details=response_details,
            **validated_data
        )

class AuthorizationResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthorizationResponse
        fields = "__all__"

class AuthorizationRequestSerializer(serializers.ModelSerializer):
    response = AuthorizationResponseSerializer(read_only=True)

    class Meta:
        model = AuthorizationRequest
        fields = ["id", "patient", "plan", "requested_service", "clinical_justification", "status", "response"]

    def create(self, validated_data):
        request = self.context.get("request")
        tenant_id = getattr(request, "tenant_id", "00000000-0000-0000-0000-000000000000")
        validated_data["tenant_id"] = tenant_id

        # Prior Authorization logic mock
        status_val = "approved"
        auth_req = AuthorizationRequest.objects.create(status=status_val, **validated_data)

        # Generate auth response immediately
        rand_num = random.randint(10000, 99999)
        AuthorizationResponse.objects.create(
            tenant_id=tenant_id,
            request=auth_req,
            authorization_number=f"AUTH-{rand_num}"
        )

        return auth_req
