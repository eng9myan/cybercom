from rest_framework import serializers

from products.cyed.meetings.models import MeetingSession


class MeetingSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeetingSession
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "summary", "action_items", "key_points",
                            "status", "created_at", "updated_at"]
