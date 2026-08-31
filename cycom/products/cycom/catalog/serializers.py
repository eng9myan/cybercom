"""
Catalog serializers. tenant_id is NOT set here — it is injected by
`TenantScopedModelViewSet.perform_create` (and explicitly on nested @action
creates in views.py), matching the Cycom convention.
"""

from rest_framework import serializers

from products.cycom.catalog.models import (
    Category,
    KitComponent,
    Product,
    ProductUnit,
    ProductVariant,
    TaxClass,
)


class CategorySerializer(serializers.ModelSerializer):
    children_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = "__all__"
        read_only_fields = ["id", "slug", "tenant_id", "created_at", "updated_at"]

    def get_children_count(self, obj):
        return obj.children.filter(is_deleted=False, is_active=True).count()


class ProductUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductUnit
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class TaxClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxClass
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class KitComponentSerializer(serializers.ModelSerializer):
    component_product_name = serializers.CharField(source="component_product.name", read_only=True)
    component_product_ref = serializers.CharField(
        source="component_product.internal_ref", read_only=True
    )

    class Meta:
        model = KitComponent
        fields = [
            "id",
            "product",
            "component_product",
            "component_product_name",
            "component_product_ref",
            "quantity_per_unit",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "product",
            "component_product_name",
            "component_product_ref",
            "created_at",
        ]


class ProductSerializer(serializers.ModelSerializer):
    variants = ProductVariantSerializer(many=True, read_only=True)
    bom_components = KitComponentSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    unit_name = serializers.CharField(source="unit.abbreviation", read_only=True)
    # internal_ref is blank-able on the model, but DRF marks it required because
    # it participates in the partial UniqueConstraint. Restore blank-optional.
    internal_ref = serializers.CharField(required=False, allow_blank=True, default="")

    class Meta:
        model = Product
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class ProductListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views — omits variants."""

    category_name = serializers.CharField(source="category.name", read_only=True)
    unit_name = serializers.CharField(source="unit.abbreviation", read_only=True)
    tax_class_rate = serializers.DecimalField(
        source="tax_class.rate",
        max_digits=5,
        decimal_places=4,
        read_only=True,
        default="0.0000",
    )

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "internal_ref",
            "barcode",
            "product_type",
            "category",
            "category_name",
            "unit",
            "unit_name",
            "sell_price",
            "cost_price",
            "track_stock",
            "min_stock_qty",
            "pos_available",
            "is_active",
            "image_url",
            "tax_class_rate",
        ]
