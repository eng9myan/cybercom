from rest_framework import serializers

from .models import AssignmentStatus


class ZoneCheckRequestSerializer(serializers.Serializer):
    lat = serializers.DecimalField(max_digits=9, decimal_places=6)
    lng = serializers.DecimalField(max_digits=9, decimal_places=6)


class AssignDriverRequestSerializer(serializers.Serializer):
    order_id = serializers.UUIDField()
    store_lat = serializers.DecimalField(max_digits=9, decimal_places=6)
    store_lng = serializers.DecimalField(max_digits=9, decimal_places=6)


class AssignBatchLegSerializer(serializers.Serializer):
    order_id = serializers.UUIDField()
    store_lat = serializers.DecimalField(max_digits=9, decimal_places=6)
    store_lng = serializers.DecimalField(max_digits=9, decimal_places=6)


class AssignBatchRequestSerializer(serializers.Serializer):
    """One driver, several pickups — e.g. the customer's food order and
    grocery order, dispatched together in a single trip."""

    legs = AssignBatchLegSerializer(many=True)

    def validate_legs(self, value):
        if len(value) < 1:
            raise serializers.ValidationError("At least one leg is required.")
        return value


class RecordEventRequestSerializer(serializers.Serializer):
    order_id = serializers.UUIDField()
    status = serializers.ChoiceField(choices=AssignmentStatus.choices)
    note = serializers.CharField(max_length=200, required=False, allow_blank=True, default="")


class TrackingEventSerializer(serializers.Serializer):
    status = serializers.CharField()
    note = serializers.CharField(allow_blank=True)
    occurred_at = serializers.DateTimeField()


class OrderTrackingSerializer(serializers.Serializer):
    assignment_id = serializers.UUIDField()
    status = serializers.CharField()
    driver_name = serializers.CharField()
    run_id = serializers.UUIDField(allow_null=True)
    timeline = TrackingEventSerializer(many=True)


class RunStopSerializer(serializers.Serializer):
    order_id = serializers.UUIDField()
    stop_order = serializers.IntegerField()
    status = serializers.CharField()


class RunStatusSerializer(serializers.Serializer):
    run_id = serializers.UUIDField()
    driver_name = serializers.CharField()
    status = serializers.CharField()
    stops = RunStopSerializer(many=True)
