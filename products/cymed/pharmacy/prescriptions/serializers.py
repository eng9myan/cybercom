from rest_framework import serializers
from .models import (
    Prescription, PrescriptionItem, MedicationOrder, MedicationOrderStatus,
    MedicationRenewal, MedicationRefill, PrescriptionAttachment, MedicationHistory
)


class PrescriptionItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrescriptionItem
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class PrescriptionAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrescriptionAttachment
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class MedicationRenewalSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicationRenewal
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at", "requested_at"]


class MedicationRefillSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicationRefill
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at", "requested_at"]


class PrescriptionSerializer(serializers.ModelSerializer):
    items = PrescriptionItemSerializer(many=True, read_only=True)
    attachments = PrescriptionAttachmentSerializer(many=True, read_only=True)
    renewals = MedicationRenewalSerializer(many=True, read_only=True)
    refills = MedicationRefillSerializer(many=True, read_only=True)
    can_refill = serializers.ReadOnlyField()

    class Meta:
        model = Prescription
        fields = "__all__"
        read_only_fields = [
            "id", "tenant_id", "created_at", "updated_at",
            "prescription_number", "prescribed_at"
        ]


class MedicationOrderStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicationOrderStatus
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at", "changed_at"]


class MedicationOrderSerializer(serializers.ModelSerializer):
    status_history = MedicationOrderStatusSerializer(many=True, read_only=True)

    class Meta:
        model = MedicationOrder
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at", "order_number"]


class MedicationHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicationHistory
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
