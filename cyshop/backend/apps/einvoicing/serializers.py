from rest_framework import serializers

from .models import EInvoiceDocument, Invoice, InvoiceLine, TaxProfile


class TaxProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxProfile
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
        extra_kwargs = {"client_secret": {"write_only": True}, "csid": {"write_only": True}}

    def create(self, v):
        v["tenant_id"] = self.context["request"].tenant_id
        return super().create(v)


class InvoiceLineSerializer(serializers.ModelSerializer):
    line_subtotal = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    line_tax = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    line_total = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    quantity = serializers.DecimalField(max_digits=15, decimal_places=4, min_value=0)
    unit_price = serializers.DecimalField(max_digits=15, decimal_places=4, min_value=0)
    tax_rate = serializers.DecimalField(max_digits=5, decimal_places=4, min_value=0, max_value=1)

    class Meta:
        model = InvoiceLine
        fields = ["id", "line_no", "description", "quantity", "unit_price",
                  "discount", "tax_rate", "line_subtotal", "line_tax", "line_total"]
        read_only_fields = ["id"]


class EInvoiceDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = EInvoiceDocument
        fields = ["id", "scheme", "status", "uuid", "icv", "pih", "invoice_hash",
                  "qr_code", "ubl_xml", "warnings", "error", "submitted_at",
                  "cleared_at", "submission_response"]
        read_only_fields = fields


class InvoiceSerializer(serializers.ModelSerializer):
    lines = InvoiceLineSerializer(many=True, required=False)
    einvoice = EInvoiceDocumentSerializer(read_only=True)

    class Meta:
        model = Invoice
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "subtotal", "tax_total", "total",
                            "created_at", "updated_at"]

    def create(self, v):
        lines = v.pop("lines", [])
        v["tenant_id"] = self.context["request"].tenant_id
        inv = super().create(v)
        for i, ld in enumerate(lines, 1):
            InvoiceLine.objects.create(invoice=inv, tenant_id=inv.tenant_id,
                                       line_no=ld.get("line_no", i), **{k: ld[k] for k in ld if k != "line_no"})
        inv.recalculate()
        return inv

    def update(self, inst, v):
        lines = v.pop("lines", None)
        inv = super().update(inst, v)
        if lines is not None:
            inv.lines.all().delete()
            for i, ld in enumerate(lines, 1):
                InvoiceLine.objects.create(invoice=inv, tenant_id=inv.tenant_id,
                                           line_no=ld.get("line_no", i), **{k: ld[k] for k in ld if k != "line_no"})
        inv.recalculate()
        return inv
