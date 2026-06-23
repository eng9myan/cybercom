from rest_framework import serializers
from .models import (
    ProviderMobileDevice,
    MobileSession,
    MobilePreferences,
    MobilePushNotification,
)


class ProviderMobileDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderMobileDevice
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at", "registered_at"]


class MobileSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MobileSession
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at", "started_at"]


class MobilePreferencesSerializer(serializers.ModelSerializer):
    class Meta:
        model = MobilePreferences
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class MobilePushNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = MobilePushNotification
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]
