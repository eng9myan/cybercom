"""ViewSets and REST actions for the DTC test catalog."""
from __future__ import annotations

from django.utils.dateparse import parse_datetime
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from . import services
from .models import DtcCategory, DtcKit, DtcOrder, DtcProduct
from .serializers import (
    DtcCategorySerializer,
    DtcKitSerializer,
    DtcOrderSerializer,
    DtcProductSerializer,
)


class DtcCategoryViewSet(viewsets.ModelViewSet):
    queryset = DtcCategory.objects.all()
    serializer_class = DtcCategorySerializer


class DtcProductViewSet(viewsets.ModelViewSet):
    queryset = DtcProduct.objects.all()
    serializer_class = DtcProductSerializer


class DtcKitViewSet(viewsets.ModelViewSet):
    queryset = DtcKit.objects.all()
    serializer_class = DtcKitSerializer


class DtcOrderViewSet(viewsets.ModelViewSet):
    queryset = DtcOrder.objects.all()
    serializer_class = DtcOrderSerializer

    @action(detail=False, methods=["post"], url_path="place")
    def place(self, request):
        order = services.place_dtc_order(
            tenant_id=request.data.get("tenant_id"),
            patient_profile_id=request.data.get("patient_profile_id"),
            product_id=request.data.get("product_id"),
            shipping_address=request.data.get("shipping_address") or {},
        )
        return Response(DtcOrderSerializer(order).data)

    @action(detail=True, methods=["post"], url_path="dispatch-kit")
    def dispatch_kit(self, request, pk=None):
        order = services.dispatch_kit(
            order_id=pk,
            kit_barcode=request.data.get("kit_barcode"),
        )
        return Response(DtcOrderSerializer(order).data)

    @action(detail=False, methods=["post"], url_path="activate-kit")
    def activate_kit(self, request):
        order = services.activate_kit(
            kit_barcode=request.data.get("kit_barcode"),
        )
        return Response(DtcOrderSerializer(order).data)

    @action(detail=True, methods=["post"], url_path="sample-received")
    def sample_received(self, request, pk=None):
        order = services.sample_received(order_id=pk)
        return Response(DtcOrderSerializer(order).data)

    @action(detail=True, methods=["post"], url_path="mark-results-ready")
    def mark_results_ready(self, request, pk=None):
        order = services.mark_results_ready(order_id=pk)
        return Response(DtcOrderSerializer(order).data)

    @action(detail=True, methods=["post"], url_path="schedule-consultation")
    def schedule_consultation(self, request, pk=None):
        at_raw = request.data.get("at")
        at = parse_datetime(at_raw) if isinstance(at_raw, str) else at_raw
        order = services.schedule_consultation(order_id=pk, at=at)
        return Response(DtcOrderSerializer(order).data)

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        order = services.cancel_order(
            order_id=pk,
            reason=request.data.get("reason", ""),
        )
        return Response(DtcOrderSerializer(order).data)
