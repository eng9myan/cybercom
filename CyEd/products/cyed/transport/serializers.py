from rest_framework import serializers

from products.cyed.transport.models import (
    Bus,
    BusLocation,
    BusRoute,
    CustomStop,
    RfidBoardingEvent,
    RouteStop,
    TransportSubscription,
    TransportZone,
)


class RouteStopSerializer(serializers.ModelSerializer):
    class Meta:
        model = RouteStop
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class BusRouteSerializer(serializers.ModelSerializer):
    stops = RouteStopSerializer(many=True, read_only=True)

    class Meta:
        model = BusRoute
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "total_distance_km", "created_at", "updated_at"]


class BusLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusLocation
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class TransportZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransportZone
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class BusSerializer(serializers.ModelSerializer):
    seats_taken = serializers.ReadOnlyField()
    seats_available = serializers.ReadOnlyField()

    class Meta:
        model = Bus
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class CustomStopSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomStop
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class TransportSubscriptionSerializer(serializers.ModelSerializer):
    custom_stops = CustomStopSerializer(many=True, read_only=True)

    class Meta:
        model = TransportSubscription
        fields = "__all__"
        # fee is always computed server-side from zone + trip type.
        read_only_fields = ["id", "tenant_id", "fee_amount", "created_at", "updated_at"]

    def validate(self, attrs):
        bus = attrs.get("assigned_bus", getattr(self.instance, "assigned_bus", None))
        status = attrs.get("status", getattr(self.instance, "status", "active"))
        if bus is not None and status == "active":
            taken = bus.subscriptions.filter(status="active")
            if self.instance is not None:
                taken = taken.exclude(pk=self.instance.pk)
            if taken.count() >= bus.capacity:
                raise serializers.ValidationError(
                    {"assigned_bus": f"{bus.identifier} is at capacity ({bus.capacity})."}
                )
        return attrs


class RfidBoardingEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = RfidBoardingEvent
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
