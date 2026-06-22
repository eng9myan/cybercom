"""
API Framework DRF serializers.
"""
from rest_framework import serializers
from .models import (
    ApiApplication, ApiCatalog, ApiContract, ApiEndpoint, ApiKey,
    ApiPolicy, ApiRateLimit, ApiScope, ApiSubscription, ApiUsage,
    ApiVersion, ApiWebhook, ApiWebhookDelivery, IdempotencyKey,
)


class ApiVersionSerializer(serializers.ModelSerializer):
    version_string = serializers.CharField(read_only=True)
    is_deprecated = serializers.BooleanField(read_only=True)

    class Meta:
        model = ApiVersion
        fields = "__all__"


class ApiCatalogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApiCatalog
        fields = "__all__"


class ApiEndpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApiEndpoint
        fields = "__all__"


class ApiScopeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApiScope
        fields = "__all__"


class ApiApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApiApplication
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at"]


class ApiKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = ApiKey
        exclude = ["key_hash"]
        read_only_fields = ["key_prefix", "key_hash", "created_at", "last_used_at", "revoked_at"]


class ApiKeyCreateSerializer(serializers.Serializer):
    application_id = serializers.UUIDField()
    name = serializers.CharField(max_length=200)
    scopes = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    expires_in_days = serializers.IntegerField(required=False, allow_null=True, min_value=1, max_value=3650)


class ApiKeyRevokeSerializer(serializers.Serializer):
    revoked_by = serializers.CharField(required=False, default="")


class ApiSubscriptionSerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = ApiSubscription
        fields = "__all__"


class ApiRateLimitSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApiRateLimit
        fields = "__all__"


class ApiPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = ApiPolicy
        fields = "__all__"


class ApiContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApiContract
        fields = "__all__"
        read_only_fields = ["schema_hash", "is_valid", "last_validated_at", "validation_errors", "created_at"]


class ApiContractValidateSerializer(serializers.Serializer):
    current_schema = serializers.DictField()


class ApiUsageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApiUsage
        fields = "__all__"


class ApiWebhookSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApiWebhook
        exclude = ["secret"]
        read_only_fields = ["failure_count", "last_delivery_at", "last_delivery_status", "created_at", "updated_at"]


class ApiWebhookDeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = ApiWebhookDelivery
        fields = "__all__"


class WebhookDispatchSerializer(serializers.Serializer):
    event_type = serializers.CharField()
    payload = serializers.DictField()
    tenant_id = serializers.UUIDField(required=False, allow_null=True)


class IdempotencyKeySerializer(serializers.ModelSerializer):
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = IdempotencyKey
        fields = "__all__"


class FHIRSearchSerializer(serializers.Serializer):
    resource_type = serializers.ChoiceField(choices=[
        "Patient", "Encounter", "Practitioner", "Observation",
        "MedicationRequest", "Appointment", "CarePlan", "DiagnosticReport",
    ])
    fhir_version = serializers.ChoiceField(choices=["R4", "R5"], default="R4")
    limit = serializers.IntegerField(required=False, default=20, min_value=1, max_value=100)
    _id = serializers.CharField(required=False)
    patient = serializers.CharField(required=False)


class OpenAPISerializer(serializers.Serializer):
    catalog_slug = serializers.SlugField()


class SDKGenerateSerializer(serializers.Serializer):
    catalog_slug = serializers.SlugField()
    language = serializers.ChoiceField(choices=["typescript", "python"])
