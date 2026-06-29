from rest_framework import serializers

from .models import Bill, BillLine, Vendor, VendorPayment


class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = [
            "id",
            "tenant_id",
            "name",
            "name_ar",
            "vendor_code",
            "tax_id",
            "payment_terms_days",
            "bank_account_iban",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class BillLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillLine
        fields = [
            "id",
            "tenant_id",
            "bill",
            "description",
            "quantity",
            "unit_price",
            "tax_rate",
            "line_total",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class BillSerializer(serializers.ModelSerializer):
    lines = BillLineSerializer(many=True, read_only=True)

    class Meta:
        model = Bill
        fields = [
            "id",
            "tenant_id",
            "vendor",
            "bill_number",
            "bill_date",
            "due_date",
            "subtotal",
            "tax_amount",
            "total_amount",
            "paid_amount",
            "status",
            "lines",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class VendorPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorPayment
        fields = [
            "id",
            "tenant_id",
            "vendor",
            "bill",
            "payment_date",
            "amount",
            "method",
            "reference",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
