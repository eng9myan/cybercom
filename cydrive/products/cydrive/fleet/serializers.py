from rest_framework import serializers

from .models import DeliveryCompany, DeliveryJob, Driver, Vehicle


class DeliveryCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryCompany
        fields = [
            "id", "tenant_id", "name", "service_areas", "cydrive_subscription_active",
            "network_status", "network_joined_at", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "network_status", "network_joined_at", "created_at", "updated_at"]


class VehicleSerializer(serializers.ModelSerializer):
    is_compliant = serializers.BooleanField(read_only=True)

    class Meta:
        model = Vehicle
        fields = [
            "id", "company", "vehicle_type", "plate_number", "capacity_kg",
            "is_temperature_controlled", "insurance_expiry", "license_expiry",
            "is_active", "is_compliant",
        ]


class DriverSerializer(serializers.ModelSerializer):
    is_eligible_for_dispatch = serializers.BooleanField(read_only=True)

    class Meta:
        model = Driver
        fields = [
            "id", "company", "user_id", "name", "phone", "license_number",
            "license_expiry", "zone", "rating", "status", "current_vehicle",
            "is_eligible_for_dispatch",
        ]


class DeliveryJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryJob
        fields = [
            "id", "company", "driver", "vehicle", "source_order_id",
            "pickup_address", "dropoff_address", "requires_temperature_control",
            "package_size", "status", "cash_collection_amount", "cash_collected",
            "proof_of_delivery", "failure_reason", "assigned_at", "picked_up_at",
            "delivered_at", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "status", "assigned_at", "picked_up_at", "delivered_at",
            "created_at", "updated_at",
        ]
