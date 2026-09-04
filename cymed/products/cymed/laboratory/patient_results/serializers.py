"""DRF serializers for patient results portal models."""
from __future__ import annotations

from rest_framework import serializers

from .models import (
    ResultAcknowledgement,
    ResultDownload,
    ResultNotification,
    ResultRelease,
)


def _phi_text():
    # EncryptedText (BinaryField storage) — keep it plain text through DRF.
    return serializers.CharField(required=False, allow_blank=True)


class ResultReleaseSerializer(serializers.ModelSerializer):
    counselling_note = _phi_text()

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
