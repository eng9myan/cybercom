from rest_framework import serializers

from .models import DispenseAudit, DispenseBatch, DispenseItem, DispenseOrder, DispenseVerification


class DispenseItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = DispenseItem
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class DispenseVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DispenseVerification
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at", "verified_at"]


class DispenseAuditSerializer(serializers.ModelSerializer):
    class Meta:
        model = DispenseAudit
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at", "performed_at"]


class DispenseOrderSerializer(serializers.ModelSerializer):
    items = DispenseItemSerializer(many=True, read_only=True)
    verifications = DispenseVerificationSerializer(many=True, read_only=True)
    audit_log = DispenseAuditSerializer(many=True, read_only=True)
    patient_name = serializers.SerializerMethodField()

    class Meta:
        model = DispenseOrder
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at", "dispense_number"]

    def get_patient_name(self, obj) -> str:
        from products.cymed.core.patients.models import Patient

        patient = Patient.objects.filter(tenant_id=obj.tenant_id, id=obj.patient_id).first()
        return f"{patient.first_name} {patient.last_name}" if patient else ""


class DispenseBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = DispenseBatch
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at", "batch_number"]
