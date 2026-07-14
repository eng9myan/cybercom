from decimal import Decimal
from rest_framework import serializers
from django.db import transaction
from apps.catalog.models import Product, ProductVariant
from apps.inventory.models import Warehouse, StockLocation
from .models import Vendor, PurchaseOrder, PurchaseOrderLine, GoodsReceipt, GoodsReceiptLine


class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = '__all__'
        read_only_fields = ['id', 'tenant_id', 'created_at', 'updated_at', 'version']


class PurchaseOrderLineSerializer(serializers.ModelSerializer):
    line_subtotal = serializers.DecimalField(max_digits=15, decimal_places=4, read_only=True)
    line_tax = serializers.DecimalField(max_digits=15, decimal_places=4, read_only=True)
    outstanding_qty = serializers.DecimalField(max_digits=15, decimal_places=4, read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = PurchaseOrderLine
        fields = [
            'id', 'order', 'product', 'product_name', 'variant',
            'quantity', 'unit_cost', 'tax_rate', 'received_qty',
            'outstanding_qty', 'line_subtotal', 'line_tax', 'notes',
        ]
        read_only_fields = ['id', 'order', 'received_qty', 'line_subtotal', 'line_tax', 'outstanding_qty']


class _POLineInputSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    variant = serializers.PrimaryKeyRelatedField(
        queryset=ProductVariant.objects.all(), required=False, allow_null=True
    )
    quantity = serializers.DecimalField(max_digits=15, decimal_places=4)
    unit_cost = serializers.DecimalField(max_digits=15, decimal_places=4, required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True, default='')


class PurchaseOrderSerializer(serializers.ModelSerializer):
    lines = PurchaseOrderLineSerializer(many=True, read_only=True)
    lines_input = _POLineInputSerializer(many=True, write_only=True, required=False)
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = [
            'id', 'vendor', 'vendor_name', 'company', 'branch', 'warehouse',
            'po_number', 'status', 'currency', 'order_date', 'expected_date',
            'subtotal', 'tax_amount', 'total', 'notes',
            'lines', 'lines_input',
            'created_at', 'updated_at', 'version',
        ]
        read_only_fields = [
            'id', 'po_number', 'status', 'subtotal', 'tax_amount', 'total',
            'created_at', 'updated_at', 'version',
        ]

    def create(self, validated_data):
        lines_input = validated_data.pop('lines_input', [])
        validated_data['tenant_id'] = self.context['request'].tenant_id
        with transaction.atomic():
            po = PurchaseOrder.objects.create(**validated_data)
            for ld in lines_input:
                product = ld['product']
                tax_rate = product.tax_class.rate if product.tax_class else Decimal('0')
                unit_cost = ld.get('unit_cost') or product.cost_price
                PurchaseOrderLine.objects.create(
                    order=po,
                    tenant_id=po.tenant_id,
                    product=product,
                    variant=ld.get('variant'),
                    quantity=ld['quantity'],
                    unit_cost=unit_cost,
                    tax_rate=tax_rate,
                    notes=ld.get('notes', ''),
                )
            if lines_input:
                po.recalculate()
        return po


class PurchaseOrderListSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)
    line_count = serializers.SerializerMethodField()

    class Meta:
        model = PurchaseOrder
        fields = [
            'id', 'po_number', 'vendor', 'vendor_name', 'status',
            'currency', 'order_date', 'expected_date', 'total', 'line_count',
            'created_at',
        ]

    def get_line_count(self, obj):
        return obj.lines.filter(is_deleted=False).count()


class GoodsReceiptLineSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = GoodsReceiptLine
        fields = [
            'id', 'receipt', 'po_line', 'product', 'product_name',
            'variant', 'received_qty', 'unit_cost',
        ]
        read_only_fields = ['id', 'receipt']


class _GRNLineInputSerializer(serializers.Serializer):
    po_line = serializers.PrimaryKeyRelatedField(queryset=PurchaseOrderLine.objects.all())
    received_qty = serializers.DecimalField(max_digits=15, decimal_places=4)
    unit_cost = serializers.DecimalField(max_digits=15, decimal_places=4, required=False, allow_null=True)


class GoodsReceiptSerializer(serializers.ModelSerializer):
    grn_lines = GoodsReceiptLineSerializer(many=True, read_only=True)
    lines_input = _GRNLineInputSerializer(many=True, write_only=True)

    class Meta:
        model = GoodsReceipt
        fields = [
            'id', 'purchase_order', 'grn_number', 'status',
            'received_at', 'warehouse', 'location', 'notes',
            'grn_lines', 'lines_input',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'grn_number', 'status', 'created_at', 'updated_at']

    def create(self, validated_data):
        lines_input = validated_data.pop('lines_input', [])
        validated_data['tenant_id'] = self.context['request'].tenant_id
        with transaction.atomic():
            grn = GoodsReceipt.objects.create(**validated_data)
            for ld in lines_input:
                po_line = ld['po_line']
                GoodsReceiptLine.objects.create(
                    receipt=grn,
                    tenant_id=grn.tenant_id,
                    po_line=po_line,
                    product=po_line.product,
                    variant=po_line.variant,
                    received_qty=ld['received_qty'],
                    unit_cost=ld.get('unit_cost') or po_line.unit_cost,
                )
            grn.post()
        return grn
