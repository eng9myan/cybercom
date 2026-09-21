from datetime import date

from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from core.viewsets import TenantScopedModelViewSet
from products.cycom.manufacturing.models import (
    BillOfMaterial,
    BOMComponent,
    ManufacturingOrder,
    Routing,
    WorkCenter,
    WorkOrder,
)
from products.cycom.manufacturing.serializers import (
    BillOfMaterialSerializer,
    BOMComponentSerializer,
    ManufacturingOrderSerializer,
    RoutingSerializer,
    WorkCenterSerializer,
    WorkOrderSerializer,
)
from products.cycom.manufacturing.services import (
    complete_manufacturing_order,
    finish_work_order,
    start_work_order,
    work_center_load,
)


class BillOfMaterialViewSet(TenantScopedModelViewSet):
    queryset = BillOfMaterial.objects.all()
    serializer_class = BillOfMaterialSerializer


class BOMComponentViewSet(TenantScopedModelViewSet):
    queryset = BOMComponent.objects.all()
    serializer_class = BOMComponentSerializer


class WorkCenterViewSet(TenantScopedModelViewSet):
    queryset = WorkCenter.objects.all()
    serializer_class = WorkCenterSerializer
    filterset_fields = ["is_active"]

    @action(detail=True, methods=["get"], url_path="load")
    def load(self, request, pk=None):
        work_center = self.get_object()
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        if not (date_from and date_to):
            raise ValidationError("date_from and date_to are required.")
        result = work_center_load(
            work_center, date_from=date.fromisoformat(date_from), date_to=date.fromisoformat(date_to)
        )
        return Response(result)


class RoutingViewSet(TenantScopedModelViewSet):
    queryset = Routing.objects.select_related("product").prefetch_related("operations__work_center").all()
    serializer_class = RoutingSerializer
    filterset_fields = ["product", "is_active"]


class WorkOrderViewSet(TenantScopedModelViewSet):
    queryset = WorkOrder.objects.select_related(
        "manufacturing_order", "routing_operation", "work_center"
    ).all()
    serializer_class = WorkOrderSerializer
    filterset_fields = ["manufacturing_order", "work_center", "status"]

    @action(detail=True, methods=["post"])
    def start(self, request, pk=None):
        wo = start_work_order(self.get_object())
        return Response(WorkOrderSerializer(wo).data)

    @action(detail=True, methods=["post"])
    def finish(self, request, pk=None):
        wo = finish_work_order(self.get_object())
        return Response(WorkOrderSerializer(wo).data)


class ManufacturingOrderViewSet(TenantScopedModelViewSet):
    queryset = ManufacturingOrder.objects.select_related("bom", "routing").prefetch_related(
        "work_orders"
    ).all()
    serializer_class = ManufacturingOrderSerializer
    filterset_fields = ["status"]

    @action(detail=True, methods=["post"], url_path="complete")
    def complete(self, request, pk=None):
        mo = self.get_object()
        complete_manufacturing_order(mo)
        return Response(ManufacturingOrderSerializer(mo).data)
