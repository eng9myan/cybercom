from decimal import Decimal
from rest_framework import serializers
from django.db import transaction
from .models import PosSession, PosOrder, PosOrderLine, PosPayment, PosReceipt, Device
from apps.catalog.models import Product, ProductVariant


class PosSessionSerializer(serializers.ModelSerializer):
    order_count = serializers.SerializerMethodField()
    total_sales = serializers.SerializerMethodField()
    cashier_username = serializers.SerializerMethodField()

    class Meta:
        model = PosSession
        fields = [
            'id', 'company', 'branch', 'cashier', 'cashier_username', 'name', 'status',
            'opening_float', 'closing_float', 'opening_at', 'closing_at',
            'notes', 'order_count', 'total_sales', 'tenant_id', 'created_at',
        ]
        read_only_fields = ['id', 'cashier', 'cashier_username', 'opening_at', 'order_count', 'total_sales', 'tenant_id', 'created_at']

    def get_order_count(self, obj):
        return obj.orders.filter(status='PAID', is_deleted=False).count()

    def get_total_sales(self, obj):
        from django.db.models import Sum
        result = obj.orders.filter(status='PAID', is_deleted=False).aggregate(t=Sum('total'))
        return str(result['t'] or Decimal('0'))

    def get_cashier_username(self, obj):
        return getattr(obj.cashier, 'username', None) if obj.cashier_id else None

    def create(self, validated_data):
        validated_data['tenant_id'] = self.context['request'].tenant_id
        return super().create(validated_data)


class PosOrderLineSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    line_subtotal = serializers.DecimalField(max_digits=15, decimal_places=4, read_only=True)
    line_tax = serializers.DecimalField(max_digits=15, decimal_places=4, read_only=True)

    class Meta:
        model = PosOrderLine
        fields = [
            'id', 'product', 'product_name', 'variant', 'quantity',
            'unit_price', 'discount_percent', 'tax_rate', 'notes',
            'line_subtotal', 'line_tax',
        ]
        read_only_fields = ['id', 'product_name', 'line_subtotal', 'line_tax']

    def create(self, validated_data):
        validated_data['tenant_id'] = self.context['request'].tenant_id
        product = validated_data.get('product')
        if product and product.tax_class:
            validated_data.setdefault('tax_rate', product.tax_class.rate)
        if 'unit_price' not in validated_data and product:
            validated_data['unit_price'] = product.sell_price
        return super().create(validated_data)


class PosPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PosPayment
        fields = ['id', 'order', 'method', 'amount', 'reference', 'change_given', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('Payment amount must be positive.')
        return value

    def create(self, validated_data):
        validated_data['tenant_id'] = self.context['request'].tenant_id
        return super().create(validated_data)


class PosReceiptSerializer(serializers.ModelSerializer):
    class Meta:
        model = PosReceipt
        fields = ['id', 'order', 'receipt_number', 'printed_at', 'emailed_at', 'qr_data', 'created_at']
        read_only_fields = ['id', 'receipt_number', 'created_at']


class PosOrderListSerializer(serializers.ModelSerializer):
    cashier_username = serializers.SerializerMethodField()
    line_count = serializers.IntegerField(source='lines.count', read_only=True)

    class Meta:
        model = PosOrder
        fields = [
            'id', 'order_number', 'status', 'source', 'cashier_username',
            'customer_name', 'subtotal', 'tax_amount', 'discount_amount',
            'total', 'line_count', 'kitchen_status', 'table_ref', 'branch', 'paid_at', 'created_at',
        ]

    def get_cashier_username(self, obj):
        return getattr(obj.cashier, 'username', None) if obj.cashier_id else None


class _LineInputSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    variant = serializers.PrimaryKeyRelatedField(
        queryset=ProductVariant.objects.all(), required=False, allow_null=True
    )
    quantity = serializers.DecimalField(max_digits=15, decimal_places=4)
    unit_price = serializers.DecimalField(max_digits=15, decimal_places=4, required=False)
    discount_percent = serializers.DecimalField(max_digits=5, decimal_places=2, default='0.00')
    notes = serializers.CharField(required=False, allow_blank=True, default='')


class PosOrderSerializer(serializers.ModelSerializer):
    lines = PosOrderLineSerializer(many=True, read_only=True)
    payments = PosPaymentSerializer(many=True, read_only=True)
    receipt = PosReceiptSerializer(read_only=True)
    cashier_username = serializers.SerializerMethodField()
    lines_input = _LineInputSerializer(many=True, write_only=True, required=False, default=list)

    class Meta:
        model = PosOrder
        fields = [
            'id', 'session', 'company', 'branch', 'cashier', 'cashier_username',
            'order_number', 'source', 'status', 'kitchen_status', 'customer_name', 'customer_phone',
            'table_ref', 'subtotal', 'discount_amount', 'tax_amount', 'total',
            'notes', 'paid_at', 'lines', 'lines_input', 'payments', 'receipt', 'created_at',
        ]
        read_only_fields = [
            'id', 'order_number', 'subtotal', 'tax_amount', 'total',
            'cashier_username', 'paid_at', 'lines', 'payments', 'receipt', 'created_at',
        ]

    def get_cashier_username(self, obj):
        return getattr(obj.cashier, 'username', None) if obj.cashier_id else None

    def create(self, validated_data):
        lines_input = validated_data.pop('lines_input', [])
        validated_data['tenant_id'] = self.context['request'].tenant_id
        with transaction.atomic():
            order = PosOrder.objects.create(**validated_data)
            for ld in lines_input:
                product = ld['product']
                tax_rate = product.tax_class.rate if product.tax_class else Decimal('0')
                unit_price = ld.get('unit_price') or product.sell_price
                PosOrderLine.objects.create(
                    order=order,
                    tenant_id=order.tenant_id,
                    product=product,
                    variant=ld.get('variant'),
                    quantity=ld['quantity'],
                    unit_price=unit_price,
                    discount_percent=ld.get('discount_percent', Decimal('0')),
                    tax_rate=tax_rate,
                    notes=ld.get('notes', ''),
                )
            if lines_input:
                order.recalculate()
        return order


class DeviceSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    device_type_display = serializers.CharField(source='get_device_type_display', read_only=True)
    route = serializers.CharField(read_only=True)

    class Meta:
        model = Device
        fields = [
            'id', 'company', 'branch', 'branch_name', 'name', 'code',
            'device_type', 'device_type_display', 'route', 'last_seen_at',
            'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'branch_name', 'device_type_display', 'route', 'last_seen_at', 'created_at']

    def create(self, validated_data):
        validated_data['tenant_id'] = self.context['request'].tenant_id
        return super().create(validated_data)
