"""CyMed Pharmacy robotics serializers."""
from rest_framework import serializers

from .models import DispenseJob, RobotBinInventory, RobotDevice, RobotEvent


class RobotDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = RobotDevice
        fields = "__all__"


class RobotBinInventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = RobotBinInventory
        fields = "__all__"


class DispenseJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = DispenseJob
        fields = "__all__"


class RobotEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = RobotEvent
        fields = "__all__"
