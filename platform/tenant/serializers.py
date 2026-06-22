"""
CyberCom Multi-Tenant Framework — DRF Serializers.
"""
from rest_framework import serializers
from .models import (
    Tenant, TenantProfile, TenantConfiguration, TenantBranding,
    TenantSubscription, TenantLicense, TenantEnvironment, TenantRegion,
    TenantDeploymentProfile, TenantFeatureFlag, TenantDomain,
    TenantSSOConfiguration, TenantStoragePolicy, TenantRetentionPolicy,
    TenantComplianceProfile, TenantAuditConfiguration,
)


class TenantProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenantProfile
        exclude = ["tenant"]
        read_only_fields = ["id", "created_at", "updated_at"]


class TenantConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenantConfiguration
        exclude = ["tenant"]
        read_only_fields = ["id", "created_at", "updated_at"]


class TenantBrandingSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenantBranding
        exclude = ["tenant"]
        read_only_fields = ["id", "created_at", "updated_at"]


class TenantSerializer(serializers.ModelSerializer):
    profile = TenantProfileSerializer(read_only=True)
    configuration = TenantConfigurationSerializer(read_only=True)
    branding = TenantBrandingSerializer(read_only=True)

    class Meta:
        model = Tenant
        fields = [
            "id", "name", "slug", "display_name", "tenant_type", "tier",
            "status", "country_code", "timezone", "locale", "home_region",
            "identity_realm_id", "keycloak_realm_name",
            "activated_at", "suspended_at", "archived_at",
            "terminated_at", "decommissioned_at", "metadata",
            "created_at", "updated_at",
            "profile", "configuration", "branding",
        ]
        read_only_fields = [
            "id", "activated_at", "suspended_at", "archived_at",
            "terminated_at", "decommissioned_at", "created_at", "updated_at",
        ]


class TenantCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = [
            "name", "slug", "display_name", "tenant_type", "tier",
            "country_code", "timezone", "locale", "home_region", "metadata",
        ]


class TenantSubscriptionSerializer(serializers.ModelSerializer):
    is_trial = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()

    class Meta:
        model = TenantSubscription
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at", "is_trial", "is_expired"]


class TenantLicenseSerializer(serializers.ModelSerializer):
    is_valid = serializers.ReadOnlyField()

    class Meta:
        model = TenantLicense
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at", "is_valid"]


class TenantEnvironmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenantEnvironment
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class TenantRegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenantRegion
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class TenantDeploymentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenantDeploymentProfile
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class TenantFeatureFlagSerializer(serializers.ModelSerializer):
    is_expired = serializers.ReadOnlyField()

    class Meta:
        model = TenantFeatureFlag
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at", "enabled_at", "is_expired"]


class TenantDomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenantDomain
        fields = "__all__"
        read_only_fields = [
            "id", "created_at", "updated_at",
            "verification_token", "verified_at", "is_verified",
        ]


class TenantSSOConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenantSSOConfiguration
        exclude = []
        read_only_fields = ["id", "created_at", "updated_at"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.pop("x509_cert", None)
        return data


class TenantStoragePolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = TenantStoragePolicy
        exclude = ["tenant"]
        read_only_fields = ["id", "created_at", "updated_at"]


class TenantRetentionPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = TenantRetentionPolicy
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class TenantComplianceProfileSerializer(serializers.ModelSerializer):
    is_current = serializers.ReadOnlyField()

    class Meta:
        model = TenantComplianceProfile
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at", "is_current"]


class TenantAuditConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenantAuditConfiguration
        exclude = ["tenant"]
        read_only_fields = ["id", "created_at", "updated_at"]


# ---------------------------------------------------------------------------
# Action serializers
# ---------------------------------------------------------------------------

class TenantBootstrapSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    slug = serializers.SlugField(max_length=100)
    display_name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    tenant_type = serializers.ChoiceField(choices=Tenant.tenant_type.field.choices, default="saas")
    tier = serializers.ChoiceField(choices=Tenant.tier.field.choices, default="shared")
    country_code = serializers.CharField(max_length=2, default="SA")
    locale = serializers.CharField(max_length=10, default="ar")
    home_region = serializers.CharField(max_length=50, default="me-central-1")
    plan = serializers.ChoiceField(choices=TenantSubscription.plan.field.choices, default="professional")
    compliance_frameworks = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    contact_email = serializers.EmailField(required=False, allow_blank=True)


class TenantSuspendSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=500, required=False, allow_blank=True)


class TenantTerminateSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=500)
    confirm = serializers.BooleanField()

    def validate_confirm(self, value):
        if not value:
            raise serializers.ValidationError("Must confirm termination.")
        return value


class TenantRealmAssignSerializer(serializers.Serializer):
    realm_id = serializers.UUIDField()
    realm_name = serializers.CharField(max_length=100)


class TenantFeatureFlagToggleSerializer(serializers.Serializer):
    key = serializers.CharField(max_length=200)
    enabled = serializers.BooleanField()
    value = serializers.JSONField(required=False, allow_null=True)


class TenantDomainVerifySerializer(serializers.Serializer):
    domain_id = serializers.UUIDField()
