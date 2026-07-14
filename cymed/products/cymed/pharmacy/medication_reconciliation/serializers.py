from rest_framework import serializers

from .models import MedicationChange, MedicationConflict, MedicationReconciliation


class MedicationChangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicationChange
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class MedicationConflictSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicationConflict
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class MedicationReconciliationSerializer(serializers.ModelSerializer):
    medication_changes = MedicationChangeSerializer(many=True, read_only=True)
    conflicts = MedicationConflictSerializer(many=True, read_only=True)

    class Meta:
        model = MedicationReconciliation
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
