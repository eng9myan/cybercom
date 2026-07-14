from rest_framework import serializers

from .models import InstallmentPlan, PatientInvoice, PaymentMethod, PaymentTransaction


class PatientInvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientInvoice
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class PaymentTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentTransaction
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {
            "gateway_token": {"write_only": True},
        }


class InstallmentPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstallmentPlan
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]
