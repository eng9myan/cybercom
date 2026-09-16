from rest_framework import serializers

from products.cyed.notifications.models import Newsletter, Notification, PushDevice


class PushDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PushDevice
        fields = "__all__"
        # The owner is taken from the token, never the body: otherwise anyone
        # could register a device against someone else's email and receive
        # their notifications.
        read_only_fields = [
            "id", "tenant_id", "created_at", "updated_at",
            "owner_email", "last_used_at", "failed_at", "failure_reason",
        ]

    def validate(self, attrs):
        platform = attrs.get("platform", getattr(self.instance, "platform", "web"))
        endpoint = attrs.get("endpoint", getattr(self.instance, "endpoint", ""))
        p256dh = attrs.get("p256dh", getattr(self.instance, "p256dh", ""))
        auth = attrs.get("auth", getattr(self.instance, "auth", ""))
        if platform == "web" and not (endpoint and p256dh and auth):
            raise serializers.ValidationError(
                "A web-push registration needs endpoint, p256dh and auth — without all "
                "three the browser cannot be reached and the device would look "
                "registered while receiving nothing."
            )
        return attrs


class NewsletterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Newsletter
        fields = "__all__"
        # Sending is an action so it happens once and deliberately.
        read_only_fields = [
            "id", "tenant_id", "created_at", "updated_at",
            "status", "sent_at", "sent_by", "recipients",
        ]

    def validate_year_levels(self, value):
        for part in [y.strip() for y in (value or "").split(",") if y.strip()]:
            if not part.isdigit():
                raise serializers.ValidationError(
                    f"'{part}' is not a year level. Use digits separated by commas."
                )
        return value


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = "__all__"
        read_only_fields = [
            "id", "tenant_id", "status", "sent_at", "read_at", "error",
            "created_at", "updated_at",
        ]
