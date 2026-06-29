from rest_framework import serializers

from .models import (
    ImagingReportAccess,
    ImagingResultView,
    ImagingShareLink,
    ImagingStudyMetadata,
)


class ImagingResultViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImagingResultView
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class ImagingStudyMetadataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImagingStudyMetadata
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class ImagingReportAccessSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImagingReportAccess
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at", "accessed_at"]


class ImagingShareLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImagingShareLink
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]
