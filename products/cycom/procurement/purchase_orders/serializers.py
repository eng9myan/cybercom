from rest_framework import serializers
from .models import PurchaseOrder, POLine, GoodsReceipt, GoodsReceiptLine


class POLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = POLine
        fields = [
            "id", "tenant_id", "po", "item_id", "quantity", "unit_price",
            "tax_rate", "line_total", "quantity_received",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class PurchaseOrderSerializer(serializers.ModelSerializer):
    lines = POLineSerializer(many=True, read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = [
            "id", "tenant_id", "po_number", "vendor_id", "po_date",
            "expected_delivery", "status", "subtotal", "tax_amount",
            "total_amount", "approved_by", "notes", "lines",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class GoodsReceiptLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoodsReceiptLine
        fields = [
            "id", "tenant_id", "goods_receipt", "po_line", "item_id",
            "quantity_received", "batch_id", "expiry_date",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class GoodsReceiptSerializer(serializers.ModelSerializer):
    lines = GoodsReceiptLineSerializer(many=True, read_only=True)

    class Meta:
        model = GoodsReceipt
        fields = [
            "id", "tenant_id", "po", "receipt_date", "received_by",
            "notes", "lines", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
