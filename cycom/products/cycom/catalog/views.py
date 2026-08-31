"""
Catalog viewsets. All inherit `TenantScopedModelViewSet`, which enforces
`IsAuthenticatedViaClaims` and filters every queryset by `request.tenant_id`,
and injects tenant_id on create. Class-level `queryset` attrs additionally
exclude soft-deleted rows.
"""

from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from core.viewsets import TenantScopedModelViewSet
from products.cycom.catalog.models import (
    Category,
    KitComponent,
    Product,
    ProductUnit,
    ProductVariant,
    TaxClass,
)
from products.cycom.catalog.serializers import (
    CategorySerializer,
    KitComponentSerializer,
    ProductListSerializer,
    ProductSerializer,
    ProductUnitSerializer,
    ProductVariantSerializer,
    TaxClassSerializer,
)


class CategoryViewSet(TenantScopedModelViewSet):
    serializer_class = CategorySerializer
    queryset = Category.objects.filter(is_deleted=False).select_related("parent")

    def get_queryset(self):
        qs = super().get_queryset()
        parent = self.request.query_params.get("parent")
        if parent == "null":
            qs = qs.filter(parent__isnull=True)
        elif parent:
            qs = qs.filter(parent=parent)
        return qs

    @action(detail=True, methods=["get"])
    def tree(self, request, pk=None):
        """Return a category with its direct children."""
        category = self.get_object()
        data = self.get_serializer(category).data
        children = category.children.filter(is_deleted=False, is_active=True)
        data["children"] = CategorySerializer(
            children, many=True, context={"request": request}
        ).data
        return Response(data)


class ProductUnitViewSet(TenantScopedModelViewSet):
    serializer_class = ProductUnitSerializer
    queryset = ProductUnit.objects.filter(is_deleted=False)


class TaxClassViewSet(TenantScopedModelViewSet):
    serializer_class = TaxClassSerializer
    queryset = TaxClass.objects.filter(is_deleted=False)


class ProductViewSet(TenantScopedModelViewSet):
    queryset = (
        Product.objects.filter(is_deleted=False)
        .select_related("category", "unit", "tax_class")
        .prefetch_related("variants")
    )

    def get_serializer_class(self):
        if self.action == "list":
            return ProductListSerializer
        return ProductSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        category = self.request.query_params.get("category")
        if category:
            qs = qs.filter(category=category)
        product_type = self.request.query_params.get("product_type")
        if product_type:
            qs = qs.filter(product_type=product_type)
        pos = self.request.query_params.get("pos_available")
        if pos is not None:
            qs = qs.filter(pos_available=pos.lower() in ("1", "true", "yes"))
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(
                Q(name__icontains=search)
                | Q(internal_ref__icontains=search)
                | Q(barcode__icontains=search)
            )
        return qs

    @action(detail=True, methods=["get", "post"])
    def variants(self, request, pk=None):
        product = self.get_object()
        if request.method == "GET":
            variants = product.variants.filter(is_deleted=False, is_active=True)
            return Response(
                ProductVariantSerializer(variants, many=True, context={"request": request}).data
            )
        serializer = ProductVariantSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save(product=product, tenant_id=request.tenant_id)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get", "post"])
    def bom(self, request, pk=None):
        """List or add bill-of-materials lines for a KIT product."""
        product = self.get_object()
        if request.method == "GET":
            components = product.bom_components.filter(is_deleted=False, is_active=True)
            return Response(
                KitComponentSerializer(components, many=True, context={"request": request}).data
            )
        serializer = KitComponentSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save(product=product, tenant_id=request.tenant_id)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProductVariantViewSet(TenantScopedModelViewSet):
    serializer_class = ProductVariantSerializer
    queryset = ProductVariant.objects.filter(is_deleted=False).select_related("product")


class KitComponentViewSet(TenantScopedModelViewSet):
    serializer_class = KitComponentSerializer
    queryset = KitComponent.objects.filter(is_deleted=False).select_related(
        "product", "component_product"
    )

    def get_queryset(self):
        qs = super().get_queryset()
        if v := self.request.query_params.get("product"):
            qs = qs.filter(product_id=v)
        return qs
