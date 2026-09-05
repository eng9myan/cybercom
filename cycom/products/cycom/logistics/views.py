from rest_framework.decorators import action
from rest_framework.response import Response

from core.viewsets import TenantScopedModelViewSet

from .models import Carrier, DeliveryOrder, Route, Shipment
from .serializers import (
    CarrierSerializer, DeliveryOrderSerializer, RouteSerializer, ShipmentSerializer,
)
from .services import recompute_delivery_order, recompute_shipment


class CarrierViewSet(TenantScopedModelViewSet):
    queryset = Carrier.objects.all()
    serializer_class = CarrierSerializer
    filterset_fields = ["mode", "is_own_fleet", "is_active"]


class ShipmentViewSet(TenantScopedModelViewSet):
    queryset = Shipment.objects.prefetch_related("delivery_orders__packages__items").all()
    serializer_class = ShipmentSerializer
    filterset_fields = ["status", "mode", "destination_country", "origin_country"]

    @action(detail=True, methods=["post"])
    def recompute(self, request, pk=None):
        shipment = self.get_object()
        for do in shipment.delivery_orders.all():
            recompute_delivery_order(do)
        recompute_shipment(shipment)
        return Response(ShipmentSerializer(shipment).data)


class DeliveryOrderViewSet(TenantScopedModelViewSet):
    queryset = DeliveryOrder.objects.prefetch_related("packages__items", "events").all()
    serializer_class = DeliveryOrderSerializer
    filterset_fields = ["status", "service_level", "destination_country", "shipment"]

    @action(detail=True, methods=["post"])
    def recompute(self, request, pk=None):
        do = recompute_delivery_order(self.get_object())
        return Response(DeliveryOrderSerializer(do).data)


class RouteViewSet(TenantScopedModelViewSet):
    queryset = Route.objects.prefetch_related("stops").all()
    serializer_class = RouteSerializer
    filterset_fields = ["status", "date", "driver_name"]
