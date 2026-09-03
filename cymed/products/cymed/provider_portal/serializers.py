from rest_framework import serializers

from .models import ProviderCredentialingStatus, ProviderPortalActivity, ProviderPortalProfile


class ProviderPortalProfileSerializer(serializers.ModelSerializer):
    provider_name = serializers.CharField(source="provider.__str__", read_only=True)
    npi = serializers.CharField(source="provider.npi", read_only=True)

    class Meta:
        model = ProviderPortalProfile
        fields = [
            "id",
            "provider",
            "provider_name",
            "npi",
            "email_verified",
            "phone_verified",
            "two_factor_enabled",
            "preferred_language",
            "theme_preference",
            "dashboard_layout",
            "quick_actions",
            "is_on_call",
            "created_at",
            "updated_at",
        ]


class ProviderPortalActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderPortalActivity
        fields = ["id", "activity_type", "description", "patient_mrn", "ip_address", "created_at"]


class ProviderCredentialingStatusSerializer(serializers.ModelSerializer):
    provider_name = serializers.CharField(source="provider.__str__", read_only=True)

    class Meta:
        model = ProviderCredentialingStatus
        fields = [
            "id",
            "provider",
            "provider_name",
            "status",
            "verified_by",
            "verified_at",
            "license_verified",
            "board_certification_verified",
            "background_check_passed",
            "malpractice_insurance_verified",
            "notes",
            "updated_at",
        ]
