"""Serializers for the image_sharing sub-app."""
from rest_framework import serializers

from .models import ExternalImport, ShareAccessLog, ShareableStudy, ShareLink


class ShareableStudySerializer(serializers.ModelSerializer):
    class Meta:
        model = ShareableStudy
        fields = "__all__"


class ShareLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShareLink
        fields = "__all__"


class ShareAccessLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShareAccessLog
        fields = "__all__"


class ExternalImportSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExternalImport
        fields = "__all__"
