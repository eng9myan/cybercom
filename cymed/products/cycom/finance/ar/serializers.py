from rest_framework import serializers

from .models import ARAgingBucket, Customer, Invoice, InvoiceLine, Payment


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = [
            "id",
            "tenant_id",
            "name",
            "name_ar",
            "customer_code",
            "tax_id",
            "credit_limit",
            "payment_terms_days",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class InvoiceLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceLine
        fields = [
            "id",
            "tenant_id",
            "invoice",
            "description",
            "quantity",
            "unit_price",
            "tax_rate",
            "line_total",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class InvoiceSerializer(serializers.ModelSerializer):
    lines = InvoiceLineSerializer(many=True, read_only=True)

    class Meta:
        model = Invoice
        fields = [
            "id",
            "tenant_id",
            "customer",
            "invoice_number",
            "invoice_date",
            "due_date",
            "subtotal",
            "tax_amount",
            "total_amount",
            "paid_amount",
            "status",
            "currency",
            "lines",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "id",
            "tenant_id",
            "customer",
            "invoice",
            "payment_date",
            "amount",
            "method",
            "reference",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ARAgingBucketSerializer(serializers.ModelSerializer):
    class Meta:
        model = ARAgingBucket
        fields = [
            "id",
            "tenant_id",
            "customer",
            "bucket_label",
            "amount",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
