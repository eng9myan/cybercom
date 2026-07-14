from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Sum
from django.core.exceptions import ValidationError
from .models import Warehouse, StockLocation, StockLevel, StockMovement, StockTransfer
from .serializers import (
    WarehouseSerializer, StockLocationSerializer,
    StockLevelSerializer, StockMovementSerializer, StockTransferSerializer,
)


class WarehouseViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = WarehouseSerializer

    def get_queryset(self):
        qs = Warehouse.objects.filter(
            tenant_id=self.request.tenant_id, is_deleted=False
        )
        company = self.request.query_params.get('company')
        if company:
            qs = qs.filter(company=company)
        branch = self.request.query_params.get('branch')
        if branch:
            qs = qs.filter(branch=branch)
        return qs.select_related('company', 'branch')

    @action(detail=True, methods=['get'])
    def locations(self, request, pk=None):
        warehouse = self.get_object()
        locs = warehouse.locations.filter(is_deleted=False, is_active=True)
        return Response(StockLocationSerializer(locs, many=True, context={'request': request}).data)


class StockLocationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = StockLocationSerializer

    def get_queryset(self):
        qs = StockLocation.objects.filter(
            tenant_id=self.request.tenant_id, is_deleted=False
        )
        warehouse = self.request.query_params.get('warehouse')
        if warehouse:
            qs = qs.filter(warehouse=warehouse)
        return qs.select_related('warehouse')


class StockLevelViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Stock levels are derived from movements — never written directly.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = StockLevelSerializer

    def get_queryset(self):
        qs = StockLevel.objects.filter(tenant_id=self.request.tenant_id)
        product = self.request.query_params.get('product')
        if product:
            qs = qs.filter(product=product)
        location = self.request.query_params.get('location')
        if location:
            qs = qs.filter(location=location)
        warehouse = self.request.query_params.get('warehouse')
        if warehouse:
            qs = qs.filter(location__warehouse=warehouse)
        below_min = self.request.query_params.get('below_min')
        if below_min and below_min.lower() in ('1', 'true'):
            from django.db.models import F
            qs = qs.filter(quantity__lt=F('product__min_stock_qty'))
        return qs.select_related('product', 'variant', 'location', 'location__warehouse')

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Aggregate total quantities per product across all locations."""
        warehouse = request.query_params.get('warehouse')
        qs = StockLevel.objects.filter(tenant_id=request.tenant_id)
        if warehouse:
            qs = qs.filter(location__warehouse=warehouse)
        data = (
            qs.values('product', 'product__name', 'product__internal_ref')
            .annotate(total_qty=Sum('quantity'), total_reserved=Sum('reserved_quantity'))
            .order_by('product__name')
        )
        return Response(list(data))


class StockMovementViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = StockMovementSerializer

    def get_queryset(self):
        qs = StockMovement.objects.filter(
            tenant_id=self.request.tenant_id, is_deleted=False
        )
        product = self.request.query_params.get('product')
        if product:
            qs = qs.filter(product=product)
        movement_type = self.request.query_params.get('movement_type')
        if movement_type:
            qs = qs.filter(movement_type=movement_type)
        warehouse = self.request.query_params.get('warehouse')
        if warehouse:
            qs = qs.filter(warehouse=warehouse)
        date_from = self.request.query_params.get('date_from')
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        date_to = self.request.query_params.get('date_to')
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)
        return qs.select_related('product', 'variant', 'from_location', 'to_location', 'warehouse')

    def update(self, request, *args, **kwargs):
        return Response(
            {'error': 'Stock movements are immutable. Create a correction movement instead.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


class StockTransferViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = StockTransferSerializer

    def get_queryset(self):
        qs = StockTransfer.objects.filter(
            tenant_id=self.request.tenant_id, is_deleted=False
        )
        status_param = self.request.query_params.get('status')
        if status_param:
            qs = qs.filter(status=status_param)
        branch = self.request.query_params.get('branch')
        if branch:
            qs = qs.filter(Q(from_branch=branch) | Q(to_branch=branch))
        return qs.select_related(
            'product', 'variant', 'from_branch', 'to_branch', 'from_location', 'to_location'
        )

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'], url_path='dispatch')
    def dispatch_transfer(self, request, pk=None):
        transfer = self.get_object()
        try:
            transfer.dispatch(user=request.user)
        except ValidationError as e:
            return Response({'error': e.messages if hasattr(e, 'messages') else str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(self.get_serializer(transfer).data)

    @action(detail=True, methods=['post'], url_path='receive')
    def receive_transfer(self, request, pk=None):
        transfer = self.get_object()
        try:
            transfer.receive(user=request.user)
        except ValidationError as e:
            return Response({'error': e.messages if hasattr(e, 'messages') else str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(self.get_serializer(transfer).data)
