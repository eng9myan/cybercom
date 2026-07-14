from rest_framework import serializers

from platform.events.models import DeadLetterEvent, EventDeliveryLog, OutboxEvent


class OutboxEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = OutboxEvent
        fields = "__all__"


class DeadLetterEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeadLetterEvent
        fields = "__all__"


class EventDeliveryLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventDeliveryLog
        fields = "__all__"


class EventReplaySerializer(serializers.Serializer):
    tenant_id = serializers.UUIDField()
    topic = serializers.CharField(max_length=500)
    start_time = serializers.DateTimeField(required=False, allow_null=True)
    end_time = serializers.DateTimeField(required=False, allow_null=True)
    event_types = serializers.ListField(child=serializers.CharField(max_length=200), required=False)
