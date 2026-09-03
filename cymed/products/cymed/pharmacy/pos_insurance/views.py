"""CyMed Pharmacy pos_insurance viewsets."""
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from . import services
from .models import (
    AdjudicationLog,
    PosSale,
    PosSaleItem,
    PosSession,
    PosTerminal,
)
from .serializers import (
    AdjudicationLogSerializer,
    PosSaleItemSerializer,
    PosSaleSerializer,
    PosSessionSerializer,
    PosTerminalSerializer,
)


class PosTerminalViewSet(viewsets.ModelViewSet):
    queryset = PosTerminal.objects.all()
    serializer_class = PosTerminalSerializer


class PosSessionViewSet(viewsets.ModelViewSet):
    queryset = PosSession.objects.all()
    serializer_class = PosSessionSerializer

    @action(detail=False, methods=["post"], url_path="open")
    def open_session_action(self, request):
        session = services.open_session(
            tenant_id=request.data.get("tenant_id"),
            terminal_id=request.data.get("terminal_id"),
            cashier_profile_id=request.data.get("cashier_profile_id"),
            opening_float=request.data.get("opening_float", "0"),
        )
        return Response(PosSessionSerializer(session).data)

    @action(detail=True, methods=["post"], url_path="close")
    def close_session_action(self, request, pk=None):
        session = services.close_session(
            session_id=pk,
            closing_cash=request.data.get("closing_cash", "0"),
        )
        return Response(PosSessionSerializer(session).data)


class PosSaleViewSet(viewsets.ModelViewSet):
    queryset = PosSale.objects.all()
    serializer_class = PosSaleSerializer

    @action(detail=False, methods=["post"], url_path="start")
    def start_sale_action(self, request):
        sale = services.start_sale(
            tenant_id=request.data.get("tenant_id"),
            session_id=request.data.get("session_id"),
            patient_profile_id=request.data.get("patient_profile_id"),
            order_id=request.data.get("order_id"),
        )
        return Response(PosSaleSerializer(sale).data)

    @action(detail=True, methods=["post"], url_path="add-item")
    def add_item_action(self, request, pk=None):
        item = services.add_item(
            sale_id=pk,
            product_id=request.data.get("product_id"),
            product_name=request.data.get("product_name"),
            qty=int(request.data.get("qty", 1)),
            unit_price=request.data.get("unit_price", "0"),
        )
        return Response(PosSaleItemSerializer(item).data)

    @action(detail=True, methods=["post"], url_path="request-adjudication")
    def request_adjudication_action(self, request, pk=None):
        sale = services.request_realtime_adjudication(
            sale_id=pk,
            insurance_policy_id=request.data.get("insurance_policy_id"),
            payer=request.data.get("payer", "nphies"),
        )
        return Response(PosSaleSerializer(sale).data)

    @action(detail=True, methods=["post"], url_path="finalize")
    def finalize_sale_action(self, request, pk=None):
        sale = services.finalize_sale(
            sale_id=pk,
            payment_ref=request.data.get("payment_ref", ""),
        )
        return Response(PosSaleSerializer(sale).data)

    @action(detail=True, methods=["post"], url_path="void")
    def void_sale_action(self, request, pk=None):
        sale = services.void_sale(sale_id=pk)
        return Response(PosSaleSerializer(sale).data)


class PosSaleItemViewSet(viewsets.ModelViewSet):
    queryset = PosSaleItem.objects.all()
    serializer_class = PosSaleItemSerializer


class AdjudicationLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AdjudicationLog.objects.all()
    serializer_class = AdjudicationLogSerializer
