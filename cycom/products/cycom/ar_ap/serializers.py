from rest_framework import serializers

from products.cycom.ar_ap.models import Invoice, InvoiceLine, Partner, Payment


class PartnerSerializer(serializers.ModelSerializer):
    # Encrypted (BinaryField storage) — declare as plain text so DRF neither
    # base64-encodes them nor exposes the companion *_bidx HMAC columns.
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True, max_length=50)
    contact_name = serializers.CharField(required=False, allow_blank=True, max_length=255)
    address = serializers.CharField(required=False, allow_blank=True, max_length=255)
    iban = serializers.CharField(required=False, allow_blank=True, max_length=64)

    class Meta:
        model = Partner
        fields = [
            "id", "tenant_id", "name", "partner_type", "email", "phone", "tax_id",
            "is_active", "legal_name_ar", "trade_name", "category", "cr_number",
            "cr_expiry", "bank_name", "bank_branch", "iban", "swift_code",
            "credit_limit", "payment_terms_days", "contact_name", "address", "city",
            "approval_status", "rejection_reason", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class InvoiceLineSerializer(serializers.ModelSerializer):
    subtotal = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    tax_amount = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = InvoiceLine
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "invoice", "created_at", "updated_at"]


class InvoiceSerializer(serializers.ModelSerializer):
    lines = InvoiceLineSerializer(many=True)
    amount_due = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = Invoice
        fields = "__all__"
        read_only_fields = [
            "id", "tenant_id", "status", "amount_subtotal", "amount_tax", "amount_total",
            "amount_paid", "journal_entry", "created_at", "updated_at",
        ]

    def validate_lines(self, lines):
        if not lines:
            raise serializers.ValidationError("Invoice must have at least one line.")
        return lines

    def create(self, validated_data):
        lines_data = validated_data.pop("lines")
        invoice = Invoice.objects.create(**validated_data)
        for line_data in lines_data:
            InvoiceLine.objects.create(
                invoice=invoice, tenant_id=validated_data["tenant_id"], **line_data
            )
        invoice.refresh_from_db()
        return invoice


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "status", "journal_entry", "created_at", "updated_at"]
