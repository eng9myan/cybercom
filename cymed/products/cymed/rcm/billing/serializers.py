from rest_framework import serializers

from .models import (
    BillingAdjustment,
    EncounterBilling,
    Invoice,
    InvoiceLine,
    PatientAccount,
    Refund,
)


class PatientAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientAccount
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class EncounterBillingSerializer(serializers.ModelSerializer):
    class Meta:
        model = EncounterBilling
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class InvoiceLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceLine
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class BillingAdjustmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillingAdjustment
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class RefundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Refund
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class InvoiceSerializer(serializers.ModelSerializer):
    lines = InvoiceLineSerializer(many=True, read_only=True)
    adjustments = BillingAdjustmentSerializer(many=True, read_only=True)
    refunds = RefundSerializer(many=True, read_only=True)

    class Meta:
        model = Invoice
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class InvoiceWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]
