from rest_framework import serializers
from .models import (
    PortalPrescriptionView,
    RefillRequest,
    MedicationInstruction,
    MedicationAdherenceLog,
)


class PortalPrescriptionViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortalPrescriptionView
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class RefillRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = RefillRequest
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'submitted_at']


class MedicationInstructionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicationInstruction
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class MedicationAdherenceLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicationAdherenceLog
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']
