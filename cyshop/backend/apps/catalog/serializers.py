from rest_framework import serializers
from .models import Category, ProductUnit, TaxClass, Product, ProductVariant, KitComponent


class CategorySerializer(serializers.ModelSerializer):
    children_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = '__all__'
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']

    def get_children_count(self, obj):
        return obj.children.filter(is_deleted=False, is_active=True).count()

    def create(self, validated_data):
        validated_data['tenant_id'] = self.context['request'].tenant_id
        return super().create(validated_data)


class ProductUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductUnit
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['tenant_id'] = self.context['request'].tenant_id
        return super().create(validated_data)


class TaxClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxClass
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['tenant_id'] = self.context['request'].tenant_id
        return super().create(validated_data)


class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['tenant_id'] = self.context['request'].tenant_id
        return super().create(validated_data)


class KitComponentSerializer(serializers.ModelSerializer):
    component_product_name = serializers.CharField(source='component_product.name', read_only=True)
    component_product_ref = serializers.CharField(source='component_product.internal_ref', read_only=True)

    class Meta:
        model = KitComponent
        fields = [
            'id', 'product', 'component_product', 'component_product_name',
            'component_product_ref', 'quantity_per_unit', 'created_at',
        ]
        read_only_fields = ['id', 'product', 'component_product_name', 'component_product_ref', 'created_at']

    def create(self, validated_data):
        validated_data['tenant_id'] = self.context['request'].tenant_id
        return super().create(validated_data)


class ProductSerializer(serializers.ModelSerializer):
    variants = ProductVariantSerializer(many=True, read_only=True)
    bom_components = KitComponentSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    unit_name = serializers.CharField(source='unit.abbreviation', read_only=True)

    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['tenant_id'] = self.context['request'].tenant_id
        return super().create(validated_data)


class ProductListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views — omits variants."""
    category_name = serializers.CharField(source='category.name', read_only=True)
    unit_name = serializers.CharField(source='unit.abbreviation', read_only=True)
    tax_class_rate = serializers.DecimalField(
        source='tax_class.rate', max_digits=5, decimal_places=4,
        read_only=True, default='0.0000',
    )

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'internal_ref', 'barcode', 'product_type',
            'category', 'category_name', 'unit', 'unit_name',
            'sell_price', 'cost_price', 'track_stock', 'min_stock_qty',
            'pos_available', 'is_active', 'image_url', 'tax_class_rate',
        ]
