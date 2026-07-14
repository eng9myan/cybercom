from rest_framework import serializers

from .models import (
    NotificationPreference,
    NotificationTemplate,
    PatientNotification,
    PushSubscription,
)


class PatientNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientNotification
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class NotificationTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationTemplate
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class PushSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PushSubscription
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]
