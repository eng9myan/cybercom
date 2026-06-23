from rest_framework import serializers
from .models import DICOMStudy, DICOMSeries, DICOMInstance, StudyArchive


class DICOMInstanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DICOMInstance
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class DICOMSeriesSerializer(serializers.ModelSerializer):
    instances = DICOMInstanceSerializer(many=True, read_only=True)

    class Meta:
        model = DICOMSeries
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class StudyArchiveSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudyArchive
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class DICOMStudySerializer(serializers.ModelSerializer):
    series = DICOMSeriesSerializer(many=True, read_only=True)

    class Meta:
        model = DICOMStudy
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
