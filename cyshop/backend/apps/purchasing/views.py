from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Vendor, PurchaseOrder, GoodsReceipt
from .serializers import (
    VendorSerializer,
    PurchaseOrderSerializer, PurchaseOrderListSerializer,
    GoodsReceiptSerializer,
)


class VendorViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = VendorSerializer

    def get_queryset(self):
        qs = Vendor.objects.filter(
            tenant_id=self.request.tenant_id, is_deleted=False
        ).select_related('company')
        if v := self.request.query_params.get('company'):
            qs = qs.filter(company_id=v)
        if v := self.request.query_params.get('search'):
            qs = qs.filter(name__icontains=v)
        return qs

    def perform_create(self, serializer):
        serializer.save(tenant_id=self.request.tenant_id)


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return PurchaseOrderListSerializer
        return PurchaseOrderSerializer

    def get_queryset(self):
        qs = PurchaseOrder.objects.filter(
            tenant_id=self.request.tenant_id, is_deleted=False
        ).select_related('vendor', 'company', 'branch', 'warehouse').prefetch_related('lines')
        p = self.request.query_params
        if v := p.get('vendor'):
            qs = qs.filter(vendor_id=v)
        if v := p.get('status'):
            qs = qs.filter(status=v)
        if v := p.get('company'):
            qs = qs.filter(company_id=v)
        if v := p.get('date_from'):
            qs = qs.filter(order_date__gte=v)
        if v := p.get('date_to'):
            qs = qs.filter(order_date__lte=v)
        return qs

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        po = self.get_object()
        if po.status != 'DRAFT':
            return Response(
                {'detail': 'Only DRAFT orders can be confirmed.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not po.lines.filter(is_deleted=False).exists():
            return Response(
                {'detail': 'Purchase order has no lines.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        po.status = 'CONFIRMED'
        po.save()
        return Response(PurchaseOrderSerializer(po, context={'request': request}).data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        po = self.get_object()
        if po.status in ('RECEIVED', 'PARTIAL'):
            return Response(
                {'detail': 'Cannot cancel an order that has already received goods.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        po.status = 'CANCELLED'
        po.save()
        return Response(PurchaseOrderSerializer(po, context={'request': request}).data)

    @action(detail=True, methods=['post'])
    def add_line(self, request, pk=None):
        from apps.catalog.models import Product
        from decimal import Decimal
        from .models import PurchaseOrderLine

        po = self.get_object()
        if po.status not in ('DRAFT', 'CONFIRMED'):
            return Response(
                {'detail': 'Cannot add lines to order in current status.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        from .serializers import _POLineInputSerializer
        ser = _POLineInputSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        product = d['product']
        tax_rate = product.tax_class.rate if product.tax_class else Decimal('0')
        unit_cost = d.get('unit_cost') or product.cost_price
        PurchaseOrderLine.objects.create(
            order=po,
            tenant_id=request.tenant_id,
            product=product,
            variant=d.get('variant'),
            quantity=d['quantity'],
            unit_cost=unit_cost,
            tax_rate=tax_rate,
            notes=d.get('notes', ''),
        )
        po.recalculate()
        return Response(
            PurchaseOrderSerializer(po, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class GoodsReceiptViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = GoodsReceiptSerializer

    def get_queryset(self):
        qs = GoodsReceipt.objects.filter(
            tenant_id=self.request.tenant_id, is_deleted=False
        ).select_related('purchase_order', 'warehouse', 'location').prefetch_related('grn_lines')
        if v := self.request.query_params.get('purchase_order'):
            qs = qs.filter(purchase_order_id=v)
        if v := self.request.query_params.get('status'):
            qs = qs.filter(status=v)
        return qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            grn = serializer.save()
        except Exception as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(self.get_serializer(grn).data, status=status.HTTP_201_CREATED)
