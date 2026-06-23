from rest_framework import serializers
from .models import AutomationDevice, DispensingRobot, CabinetDevice, AutomationQueue


class DispensingRobotSerializer(serializers.ModelSerializer):
    class Meta:
        model = DispensingRobot
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class CabinetDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CabinetDevice
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class AutomationDeviceSerializer(serializers.ModelSerializer):
    robot_profile = DispensingRobotSerializer(read_only=True)
    cabinet_profile = CabinetDeviceSerializer(read_only=True)

    class Meta:
        model = AutomationDevice
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class AutomationQueueSerializer(serializers.ModelSerializer):
    device_name = serializers.CharField(source="device.device_name", read_only=True)

    class Meta:
        model = AutomationQueue
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
