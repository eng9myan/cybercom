from rest_framework import serializers
from products.cymed.commercial.licensing.models import (
    License, LicenseKey, LicenseActivation, LicenseFeature,
    LicenseAudit, LicenseUsage, LicenseServer, OfflineActivationPackage
)


class LicenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = License
        fields = "__all__"


class LicenseKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = LicenseKey
        fields = "__all__"


class LicenseActivationSerializer(serializers.ModelSerializer):
    class Meta:
        model = LicenseActivation
        fields = "__all__"


class LicenseFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = LicenseFeature
        fields = "__all__"


class LicenseAuditSerializer(serializers.ModelSerializer):
    class Meta:
        model = LicenseAudit
        fields = "__all__"


class LicenseUsageSerializer(serializers.ModelSerializer):
    class Meta:
        model = LicenseUsage
        fields = "__all__"


class LicenseServerSerializer(serializers.ModelSerializer):
    class Meta:
        model = LicenseServer
        fields = "__all__"


class OfflineActivationPackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfflineActivationPackage
        fields = "__all__"


class LicenseActivateSerializer(serializers.Serializer):
    """Used for the /activate/ action."""
    license_key = serializers.CharField()
    machine_fingerprint = serializers.CharField(required=False, allow_blank=True)
    deployment_profile_code = serializers.CharField(required=False, allow_blank=True)
    is_online = serializers.BooleanField(default=True)


class LicenseValidateSerializer(serializers.Serializer):
    """Used for the /validate/ action — checks if a license is active."""
    license_number = serializers.CharField()
    product_code = serializers.CharField()
