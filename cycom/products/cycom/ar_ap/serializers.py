from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from products.cycom.accounting.sequencing import (
    INVOICE_TYPE_TO_DOC_TYPE,
    allocate_document_number,
    can_override_document_number,
)
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

    def validate_quantity(self, value):
        # A-2: a negative-quantity line is an uncontrolled back-door credit
        # note (no separate numbering, no approval, no e-invoice credit-note
        # handling). Reversals go through a real CreditNote (invoice_type
        # *_credit_note), never a negative line on an ordinary invoice.
        if value is not None and value <= 0:
            raise serializers.ValidationError("Line quantity must be greater than zero.")
        return value

    def validate_unit_price(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Line unit price cannot be negative.")
        return value


class InvoiceSerializer(serializers.ModelSerializer):
    lines = InvoiceLineSerializer(many=True)
    amount_due = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    # A-4: number is auto-allocated from a per-tenant/per-type gapless sequence
    # when omitted. A caller with a finance/admin role may still supply one
    # explicitly (migration, correction) — see validate().
    number = serializers.CharField(required=False, allow_blank=True, max_length=100)

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

    def _tenant_id(self):
        req = self.context.get("request")
        return getattr(req, "tenant_id", None) if req else None

    def validate(self, attrs):
        # A-4: a manually supplied number is a privileged override of the auto
        # sequence — allow it only for finance/admin roles (or non-API callers
        # with no request context, e.g. data migrations).
        request = self.context.get("request")
        if attrs.get("number") and request is not None and not can_override_document_number(request):
            raise serializers.ValidationError(
                {"number": "You are not allowed to set the document number manually; "
                           "leave it blank to have it auto-generated."}
            )

        # A-1: reject a duplicate document number up front with a clean field
        # error, instead of letting it hit the DB unique constraint
        # (Invoice.Meta.unique_together = (tenant_id, number)) and surface as
        # an uncaught IntegrityError / 500 (+ debug-page leak).
        number = attrs.get("number")
        tenant_id = self._tenant_id()
        if number and tenant_id:
            qs = Invoice.objects.filter(tenant_id=tenant_id, number=number)
            if self.instance is not None:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    {"number": f"An invoice/bill with number '{number}' already exists for this tenant."}
                )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        lines_data = validated_data.pop("lines")
        # A-4: auto-allocate a gapless number when the caller didn't supply one.
        # Allocation shares this transaction, so a later failure rolls the
        # counter back too — no burned numbers.
        if not validated_data.get("number"):
            doc_type = INVOICE_TYPE_TO_DOC_TYPE.get(
                validated_data["invoice_type"], "customer_invoice"
            )
            validated_data["number"] = allocate_document_number(
                validated_data["tenant_id"], doc_type, when=validated_data.get("date")
            )
        invoice = Invoice.objects.create(**validated_data)
        subtotal = Decimal("0")
        tax_total = Decimal("0")
        for line_data in lines_data:
            line = InvoiceLine.objects.create(
                invoice=invoice, tenant_id=validated_data["tenant_id"], **line_data
            )
            subtotal += line.subtotal
            tax_total += line.tax_amount
        # A-5: populate header totals from the lines on create, so a draft
        # invoice shows real amounts to a reviewer/approver (previously 0.00
        # until posting) and 3-way match can read amount_subtotal.
        invoice.amount_subtotal = subtotal.quantize(Decimal("0.01"))
        invoice.amount_tax = tax_total.quantize(Decimal("0.01"))
        invoice.amount_total = (subtotal + tax_total).quantize(Decimal("0.01"))
        invoice.save(update_fields=["amount_subtotal", "amount_tax", "amount_total"])
        invoice.refresh_from_db()
        return invoice


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "status", "journal_entry", "created_at", "updated_at"]
