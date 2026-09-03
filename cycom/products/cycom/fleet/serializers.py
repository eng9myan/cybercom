from rest_framework import serializers

from products.cycom.fleet.models import FuelLog, MaintenanceLog, Vehicle


class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = [
            "id", "name", "license_plate", "make", "model", "driver_name",
            "odometer_km", "status", "insurance_expiry", "license_expiry",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

    def validate(self, attrs):
        # Odometer only moves forward — same guard the UI enforces client-side.
        new_odo = attrs.get("odometer_km")
        if self.instance is not None and new_odo is not None and new_odo < self.instance.odometer_km:
            raise serializers.ValidationError(
                {"odometer_km": f"Cannot decrease odometer below {self.instance.odometer_km} km."}
            )
        return attrs


class MaintenanceLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaintenanceLog
        fields = [
            "id", "vehicle", "maintenance_date", "maintenance_type", "cost",
            "service_provider", "odometer_km", "next_service_km", "notes",
            "created_at",
        ]
        read_only_fields = ["id", "tenant_id", "created_at"]


class FuelLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = FuelLog
        fields = [
            "id", "vehicle", "log_date", "liters", "price_per_liter",
            "total_cost", "fuel_station", "odometer_km", "created_at",
        ]
        read_only_fields = ["id", "tenant_id", "created_at"]
