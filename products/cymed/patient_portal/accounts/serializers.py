from rest_framework import serializers

from .models import (
    PatientDevice,
    PatientPortalAccount,
    PatientPreferences,
    PatientProfile,
    PatientSecuritySettings,
)


class PatientPortalAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientPortalAccount
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at", "login_count"]


class PatientProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientProfile
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class PatientPreferencesSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientPreferences
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class PatientSecuritySettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientSecuritySettings
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at", "failed_login_count", "locked_until"]


class PatientDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientDevice
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at", "registered_at"]


class PatientPortalAccountDetailSerializer(serializers.ModelSerializer):
    """Full account detail including nested related objects."""

    profile = PatientProfileSerializer(read_only=True)
    preferences = PatientPreferencesSerializer(read_only=True)
    security_settings = PatientSecuritySettingsSerializer(read_only=True)
    devices = PatientDeviceSerializer(many=True, read_only=True)

    class Meta:
        model = PatientPortalAccount
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at", "login_count"]
