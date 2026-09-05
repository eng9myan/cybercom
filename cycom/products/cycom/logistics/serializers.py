from rest_framework import serializers

from .models import (
    Carrier, DeliveryEvent, DeliveryOrder, Package, PackageItem, Route, RouteStop, Shipment,
)


class CarrierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Carrier
        fields = ["id", "name", "code", "mode", "scac", "is_own_fleet", "is_active"]
        read_only_fields = ["id", "tenant_id"]


class PackageItemSerializer(serializers.ModelSerializer):
    line_net_weight_kg = serializers.DecimalField(max_digits=12, decimal_places=3, read_only=True)

    class Meta:
        model = PackageItem
        fields = ["id", "sku", "description", "quantity", "unit_net_weight_kg", "line_net_weight_kg"]
        read_only_fields = ["id", "tenant_id"]


class PackageSerializer(serializers.ModelSerializer):
    items = PackageItemSerializer(many=True, read_only=True)
    volume_m3 = serializers.DecimalField(max_digits=12, decimal_places=4, read_only=True)
    volumetric_weight_kg = serializers.DecimalField(max_digits=10, decimal_places=3, read_only=True)

    class Meta:
        model = Package
        fields = ["id", "package_no", "packaging_type", "net_weight_kg", "tare_weight_kg",
                  "gross_weight_kg", "length_cm", "width_cm", "height_cm",
                  "contents_description", "volume_m3", "volumetric_weight_kg", "items"]
        read_only_fields = ["id", "tenant_id", "gross_weight_kg"]


class DeliveryEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryEvent
        fields = ["id", "event_type", "occurred_at", "location", "notes", "pod_name", "pod_reference"]
        read_only_fields = ["id", "tenant_id"]


class DeliveryOrderSerializer(serializers.ModelSerializer):
    packages = PackageSerializer(many=True, read_only=True)
    events = DeliveryEventSerializer(many=True, read_only=True)
    on_time = serializers.BooleanField(read_only=True)

    class Meta:
        model = DeliveryOrder
        fields = ["id", "number", "shipment", "sales_order_number", "customer_name",
                  "customer_reference", "destination_city", "destination_country", "status",
                  "service_level", "promised_date", "dispatched_at", "delivered_at",
                  "failure_reason", "attempts", "net_weight_kg", "gross_weight_kg", "volume_m3",
                  "package_count", "quantity", "on_time", "packages", "events", "created_at"]
        read_only_fields = ["id", "tenant_id", "net_weight_kg", "gross_weight_kg", "volume_m3",
                            "package_count", "quantity", "created_at"]


class RouteStopSerializer(serializers.ModelSerializer):
    class Meta:
        model = RouteStop
        fields = ["id", "sequence", "stop_type", "delivery_order", "address", "planned_eta",
                  "actual_arrival", "dwell_minutes", "distance_from_prev_km", "status"]
        read_only_fields = ["id", "tenant_id"]


class RouteSerializer(serializers.ModelSerializer):
    stops = RouteStopSerializer(many=True, read_only=True)
    load_factor = serializers.FloatField(read_only=True)

    class Meta:
        model = Route
        fields = ["id", "date", "name", "driver_name", "vehicle_label", "status",
                  "planned_distance_km", "actual_distance_km", "planned_stops", "completed_stops",
                  "failed_stops", "load_weight_kg", "vehicle_capacity_kg", "fuel_cost",
                  "started_at", "ended_at", "load_factor", "stops"]
        read_only_fields = ["id", "tenant_id"]


class ShipmentSerializer(serializers.ModelSerializer):
    delivery_orders = DeliveryOrderSerializer(many=True, read_only=True)

    class Meta:
        model = Shipment
        fields = ["id", "number", "carrier", "mode", "incoterm", "status", "origin_name",
                  "origin_country", "destination_name", "destination_country", "planned_pickup",
                  "planned_delivery", "actual_pickup", "actual_delivery", "total_net_weight_kg",
                  "total_gross_weight_kg", "total_volume_m3", "total_packages", "total_quantity",
                  "freight_cost", "currency", "notes", "delivery_orders", "created_at"]
        read_only_fields = ["id", "tenant_id", "total_net_weight_kg", "total_gross_weight_kg",
                            "total_volume_m3", "total_packages", "total_quantity", "created_at"]
