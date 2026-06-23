from rest_framework import serializers
from .models import (
    MedicalRecordAccess,
    SharedRecord,
    RecordDownloadHistory,
    PatientDocument,
)


class MedicalRecordAccessSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalRecordAccess
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'accessed_at']


class SharedRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = SharedRecord
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'access_count']


class RecordDownloadHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = RecordDownloadHistory
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'downloaded_at']


class PatientDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientDocument
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']
