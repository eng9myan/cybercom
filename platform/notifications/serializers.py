from rest_framework import serializers
from .models import Notification, NotificationTemplate


class NotificationTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationTemplate
        fields = [
            "id", "name", "channel", "subject", "body_ar", "body_en", "is_active",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id", "template", "channel", "recipient_id", "recipient_address",
            "subject", "body", "status", "scheduled_at", "sent_at", "metadata",
            "created_at",
        ]
        read_only_fields = ["id", "status", "sent_at", "created_at"]


class SendNotificationSerializer(serializers.Serializer):
    recipient_id = serializers.CharField(max_length=255)
    recipient_address = serializers.CharField(max_length=500)
    channel = serializers.ChoiceField(choices=["email", "sms", "push", "in_app", "webhook"])
    subject = serializers.CharField(max_length=500, required=False, allow_blank=True)
    body = serializers.CharField()
    scheduled_at = serializers.DateTimeField(required=False, allow_null=True)
    metadata = serializers.DictField(required=False, default=dict)


class SendFromTemplateSerializer(serializers.Serializer):
    template_name = serializers.CharField(max_length=200)
    channel = serializers.ChoiceField(choices=["email", "sms", "push", "in_app", "webhook"])
    recipient_id = serializers.CharField(max_length=255)
    recipient_address = serializers.CharField(max_length=500)
    context = serializers.DictField(default=dict)
    lang = serializers.ChoiceField(choices=["en", "ar"], default="en")
