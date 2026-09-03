"""DRF serializers for CyMed MRFF offline_kit sub-app."""
from __future__ import annotations

from rest_framework import serializers

from .models import (
    ConflictResolution,
    OfflineCdssRun,
    OfflineDevice,
    OfflineIntake,
    SyncQueueItem,
)


class OfflineDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfflineDevice
        fields = "__all__"


class OfflineIntakeSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfflineIntake
        fields = "__all__"


class SyncQueueItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = SyncQueueItem
        fields = "__all__"


class ConflictResolutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConflictResolution
        fields = "__all__"


class OfflineCdssRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfflineCdssRun
        fields = "__all__"
