from rest_framework import serializers

from .models import ZATCAInvoice


class ZATCAInvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ZATCAInvoice
        fields = [
            "id",
            "invoice_number",
            "invoice_type",
            "patient_mrn",
            "provider_npi",
            "total_amount",
            "vat_amount",
            "total_with_vat",
            "currency",
            "status",
            "zatca_invoice_uuid",
            "qr_code_data",
            "submitted_at",
            "cleared_at",
            "created_at",
        ]
