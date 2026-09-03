from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from . import services
from .models import ClinicOrder, ClinicOrderItem, ClinicProduct


class ClinicProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClinicProduct
        fields = "__all__"


class ClinicOrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClinicOrderItem
        fields = ["id", "product", "qty", "unit_price", "amount"]


class ClinicOrderSerializer(serializers.ModelSerializer):
    items = ClinicOrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = ClinicOrder
        fields = "__all__"


class ClinicProductViewSet(viewsets.ModelViewSet):
    queryset = ClinicProduct.objects.filter(active=True)
    serializer_class = ClinicProductSerializer


class ClinicOrderViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ClinicOrder.objects.all()
    serializer_class = ClinicOrderSerializer

    @action(detail=False, methods=["post"], url_path="add-to-cart")
    def add_to_cart(self, request):
        return Response(ClinicOrderSerializer(services.add_to_cart(
            tenant_id=request.data["tenant_id"],
            patient_profile_id=request.data["patient_profile_id"],
            product_id=request.data["product_id"],
            qty=int(request.data.get("qty", 1)),
        )).data, status=201)

    @action(detail=True, methods=["post"], url_path="place")
    def place(self, request, pk=None):
        return Response(ClinicOrderSerializer(services.place_order(
            order_id=pk, delivery_address=request.data.get("delivery_address", ""),
        )).data)

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        return Response(ClinicOrderSerializer(services.cancel_order(order_id=pk)).data)

    @action(detail=True, methods=["post"], url_path="ship")
    def ship(self, request, pk=None):
        return Response(ClinicOrderSerializer(services.mark_shipped(order_id=pk)).data)

    @action(detail=True, methods=["post"], url_path="deliver")
    def deliver(self, request, pk=None):
        return Response(ClinicOrderSerializer(services.mark_delivered(order_id=pk)).data)
