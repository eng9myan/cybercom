from rest_framework import serializers

from .models import SettlementLedgerEntry


class SettlementLedgerEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = SettlementLedgerEntry
        fields = [
            "id",
            "order_id",
            "tenant_id",
            "customer_payment",
            "merchant_merchandise_revenue",
            "taxes",
            "merchant_funded_discount",
            "cybercom_funded_discount",
            "cymart_commission",
            "delivery_fee",
            "delivery_company_amount",
            "payment_processing_fee",
            "tip",
            "net_merchant_settlement",
            "net_delivery_company_settlement",
            "cybercom_net_revenue",
            "is_refund_adjustment",
            "adjusts",
            "breakdown",
            "created_at",
        ]
        read_only_fields = fields
