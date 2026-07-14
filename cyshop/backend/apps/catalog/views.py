from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .models import Category, ProductUnit, TaxClass, Product, ProductVariant, KitComponent
from .serializers import (
    CategorySerializer, ProductUnitSerializer, TaxClassSerializer,
    ProductSerializer, ProductListSerializer, ProductVariantSerializer, KitComponentSerializer,
)


class CategoryViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CategorySerializer

    def get_queryset(self):
        qs = Category.objects.filter(
            tenant_id=self.request.tenant_id, is_deleted=False
        )
        company = self.request.query_params.get('company')
        if company:
            qs = qs.filter(company=company)
        parent = self.request.query_params.get('parent')
        if parent == 'null':
            qs = qs.filter(parent__isnull=True)
        elif parent:
            qs = qs.filter(parent=parent)
        return qs.select_related('parent', 'company')

    @action(detail=True, methods=['get'])
    def tree(self, request, pk=None):
        """Return a category with its direct children."""
        category = self.get_object()
        data = self.get_serializer(category).data
        children = category.children.filter(is_deleted=False, is_active=True)
        data['children'] = CategorySerializer(children, many=True, context={'request': request}).data
        return Response(data)


class ProductUnitViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ProductUnitSerializer

    def get_queryset(self):
        return ProductUnit.objects.filter(
            tenant_id=self.request.tenant_id, is_deleted=False
        )


class TaxClassViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = TaxClassSerializer

    def get_queryset(self):
        return TaxClass.objects.filter(
            tenant_id=self.request.tenant_id, is_deleted=False
        )


class ProductViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return ProductListSerializer
        return ProductSerializer

    def get_queryset(self):
        qs = Product.objects.filter(
            tenant_id=self.request.tenant_id, is_deleted=False
        )
        # Optional filters
        company = self.request.query_params.get('company')
        if company:
            qs = qs.filter(company=company)
        category = self.request.query_params.get('category')
        if category:
            qs = qs.filter(category=category)
        product_type = self.request.query_params.get('product_type')
        if product_type:
            qs = qs.filter(product_type=product_type)
        pos = self.request.query_params.get('pos_available')
        if pos is not None:
            qs = qs.filter(pos_available=pos.lower() in ('1', 'true', 'yes'))
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(internal_ref__icontains=search) |
                Q(barcode__icontains=search)
            )
        return qs.select_related('category', 'unit', 'tax_class').prefetch_related('variants')

    @action(detail=True, methods=['get', 'post'])
    def variants(self, request, pk=None):
        product = self.get_object()
        if request.method == 'GET':
            variants = product.variants.filter(is_deleted=False, is_active=True)
            return Response(ProductVariantSerializer(variants, many=True, context={'request': request}).data)
        serializer = ProductVariantSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(product=product)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get', 'post'])
    def bom(self, request, pk=None):
        """List or add bill-of-materials lines for a KIT product."""
        product = self.get_object()
        if request.method == 'GET':
            components = product.bom_components.filter(is_deleted=False, is_active=True)
            return Response(KitComponentSerializer(components, many=True, context={'request': request}).data)
        serializer = KitComponentSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(product=product)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProductVariantViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ProductVariantSerializer

    def get_queryset(self):
        return ProductVariant.objects.filter(
            tenant_id=self.request.tenant_id, is_deleted=False
        ).select_related('product')


class KitComponentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = KitComponentSerializer

    def get_queryset(self):
        qs = KitComponent.objects.filter(
            tenant_id=self.request.tenant_id, is_deleted=False
        ).select_related('product', 'component_product')
        if v := self.request.query_params.get('product'):
            qs = qs.filter(product_id=v)
        return qs
