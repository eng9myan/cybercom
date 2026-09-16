from rest_framework import serializers

from core.serializers import ReadOnlyModelSerializer

from products.cyed.procurement.models import (
    ApprovalStep, GoodsReceipt, GoodsReceiptLine, PurchaseOrder, PurchaseOrderLine,
    PurchaseRequest, PurchaseRequestLine, Supplier,
)


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class PurchaseOrderLineSerializer(serializers.ModelSerializer):
    line_total = serializers.ReadOnlyField()
    quantity_outstanding = serializers.ReadOnlyField()

    class Meta:
        model = PurchaseOrderLine
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at", "quantity_received"]


class PurchaseOrderSerializer(serializers.ModelSerializer):
    lines = PurchaseOrderLineSerializer(many=True, read_only=True)
    total = serializers.ReadOnlyField()
    supplier_name = serializers.SerializerMethodField()

    class Meta:
        model = PurchaseOrder
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

    def get_supplier_name(self, obj):
        return obj.supplier.name if obj.supplier_id else ""


class PurchaseRequestLineSerializer(serializers.ModelSerializer):
    line_total = serializers.ReadOnlyField()

    class Meta:
        model = PurchaseRequestLine
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class ApprovalStepSerializer(ReadOnlyModelSerializer):
    class Meta:
        model = ApprovalStep
        fields = "__all__"


class PurchaseRequestSerializer(serializers.ModelSerializer):
    lines = PurchaseRequestLineSerializer(many=True, read_only=True)
    approvals = ApprovalStepSerializer(many=True, read_only=True)
    estimated_total = serializers.ReadOnlyField()
    needs_second_approval = serializers.ReadOnlyField()

    class Meta:
        model = PurchaseRequest
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at", "status", "purchase_order"]


class GoodsReceiptLineSerializer(ReadOnlyModelSerializer):
    line_value = serializers.ReadOnlyField()

    class Meta:
        model = GoodsReceiptLine
        fields = "__all__"


class GoodsReceiptSerializer(ReadOnlyModelSerializer):
    lines = GoodsReceiptLineSerializer(many=True, read_only=True)
    total_value = serializers.ReadOnlyField()

    class Meta:
        model = GoodsReceipt
        fields = "__all__"
