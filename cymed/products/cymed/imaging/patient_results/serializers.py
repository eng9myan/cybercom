"""Serializers for patient imaging results sub-app."""
from __future__ import annotations

from rest_framework import serializers

from .models import (
    ImageAccessGrant,
    ReportAcknowledgement,
    ReportDownload,
    ReportRelease,
)


class ReportReleaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportRelease
        fields = "__all__"


class ImageAccessGrantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageAccessGrant
        fields = "__all__"


class ReportDownloadSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportDownload
        fields = "__all__"


class ReportAcknowledgementSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportAcknowledgement
        fields = "__all__"
