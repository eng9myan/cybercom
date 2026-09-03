from rest_framework import serializers

from .models import JoFawTraInvoice


class JoFawTraInvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = JoFawTraInvoice
        fields = [
            "id",
            "invoice_number",
            "patient_mrn",
            "provider_npi",
            "total_amount",
            "tax_amount",
            "currency",
            "status",
            "jofawtra_invoice_id",
            "submitted_at",
            "validated_at",
            "created_at",
        ]
