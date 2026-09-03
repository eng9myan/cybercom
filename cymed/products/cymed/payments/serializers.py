from rest_framework import serializers

from .models import (
    BillLineItem,
    EligibilityCheck,
    InsurancePolicy,
    Installment,
    PatientWallet,
    PaymentMethod,
    PaymentRequest,
    PaymentTransaction,
    PreAuthorization,
    UnifiedBill,
)


class PatientWalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientWallet
        fields = ["id", "profile", "currency", "balance", "top_up_locked", "updated_at"]
        read_only_fields = ["id", "balance", "updated_at"]


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = ["id", "type", "brand", "last4", "gateway", "gateway_token",
                  "holder_name", "is_default", "expires_at"]
        extra_kwargs = {"gateway_token": {"write_only": True}}


class InsurancePolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = InsurancePolicy
        fields = ["id", "insurer_code", "policy_number", "member_no",
                  "network_tier", "deductible", "deductible_met",
                  "co_pay_percent", "co_pay_fixed", "valid_from", "valid_to",
                  "pre_auth_required", "excluded_services",
                  "verified_at", "verified_via"]
        read_only_fields = ["id", "verified_at", "verified_via"]


class EligibilityCheckSerializer(serializers.ModelSerializer):
    class Meta:
        model = EligibilityCheck
        fields = ["id", "policy", "service_code", "provider_tenant_id",
                  "covered", "co_pay_amount", "requires_preauth",
                  "checked_at", "raw_response"]
        read_only_fields = fields


class PreAuthorizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PreAuthorization
        fields = ["id", "policy", "provider_tenant_id", "service_code",
                  "clinical_justification", "status", "reference_number",
                  "approved_amount", "approved_at", "expires_at",
                  "raw_response", "created_at"]
        read_only_fields = ["id", "status", "reference_number",
                             "approved_amount", "approved_at", "expires_at",
                             "raw_response", "created_at"]


class BillLineItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillLineItem
        fields = ["id", "provider_tenant_id", "encounter_id",
                  "service_code", "service_name", "quantity",
                  "unit_price", "amount", "vat", "category",
                  "insurance_paid"]


class UnifiedBillSerializer(serializers.ModelSerializer):
    line_items = BillLineItemSerializer(many=True, read_only=True)

    class Meta:
        model = UnifiedBill
        fields = ["id", "bill_number", "patient_profile", "encounter_ids",
                  "subtotal", "vat", "total", "insurance_paid", "patient_due",
                  "status", "zatca_qr", "zatca_uuid",
                  "jofotara_qr", "jofotara_uuid",
                  "issued_at", "paid_at", "created_at", "line_items"]
        read_only_fields = ["id", "bill_number", "subtotal", "vat", "total",
                             "insurance_paid", "patient_due", "status",
                             "zatca_qr", "zatca_uuid",
                             "jofotara_qr", "jofotara_uuid",
                             "issued_at", "paid_at", "created_at", "line_items"]


class PaymentTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentTransaction
        fields = ["id", "txn_number", "bill", "payer_profile", "payee_profile",
                  "payment_method", "amount", "currency", "method_type",
                  "status", "gateway_reference", "on_behalf_note",
                  "delegation_id", "completed_at", "created_at"]
        read_only_fields = fields


class PaymentRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentRequest
        fields = ["id", "bill", "requester_profile", "payer_phone", "payer_email",
                  "amount", "token", "expires_at", "used_at"]
        read_only_fields = ["id", "token", "used_at"]


class InstallmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Installment
        fields = "__all__"
