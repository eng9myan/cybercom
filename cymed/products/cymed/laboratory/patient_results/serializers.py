"""DRF serializers for patient results portal models."""
from __future__ import annotations

from rest_framework import serializers

from .models import (
    ResultAcknowledgement,
    ResultDownload,
    ResultNotification,
    ResultRelease,
)


class ResultReleaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultRelease
        fields = "__all__"


class ResultDownloadSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultDownload
        fields = "__all__"


class ResultNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultNotification
        fields = "__all__"


class ResultAcknowledgementSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultAcknowledgement
        fields = "__all__"
