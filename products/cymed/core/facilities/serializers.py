from rest_framework import serializers
from products.cymed.core.facilities.models import (
    Facility, Building, Floor, Department, Ward, Room, Bed
)

class BedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bed
        fields = ["id", "bed_number", "status"]

class RoomSerializer(serializers.ModelSerializer):
    beds = BedSerializer(many=True, required=False)

    class Meta:
        model = Room
        fields = ["id", "room_number", "room_type", "beds"]

class WardSerializer(serializers.ModelSerializer):
    rooms = RoomSerializer(many=True, required=False)

    class Meta:
        model = Ward
        fields = ["id", "name", "code", "rooms"]

class DepartmentSerializer(serializers.ModelSerializer):
    wards = WardSerializer(many=True, required=False)

    class Meta:
        model = Department
        fields = ["id", "name", "code", "wards"]

class FloorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Floor
        fields = ["id", "name", "level"]

class BuildingSerializer(serializers.ModelSerializer):
    floors = FloorSerializer(many=True, required=False)

    class Meta:
        model = Building
        fields = ["id", "name", "code", "floors"]

class FacilitySerializer(serializers.ModelSerializer):
    buildings = BuildingSerializer(many=True, required=False)
    departments = DepartmentSerializer(many=True, required=False)

    class Meta:
        model = Facility
        fields = ["id", "organization", "name", "code", "is_active", "buildings", "departments", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]

    def create(self, validated_data):
        buildings_data = validated_data.pop("buildings", [])
        departments_data = validated_data.pop("departments", [])

        request = self.context.get("request")
        if request and hasattr(request, "tenant_id"):
            validated_data["tenant_id"] = request.tenant_id

        fac = Facility.objects.create(**validated_data)

        for b_data in buildings_data:
            Building.objects.create(facility=fac, tenant_id=fac.tenant_id, **b_data)
        for d_data in departments_data:
            Department.objects.create(facility=fac, tenant_id=fac.tenant_id, **d_data)

        return fac
