from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from core.viewsets import TenantScopedModelViewSet
from products.cycom.inventory.models import Product, Warehouse
from products.cycom.rental.models import RentalOrder, RentalOrderLine
from products.cycom.rental.serializers import RentalOrderLineSerializer, RentalOrderSerializer
from products.cycom.rental.services import (
    add_rental_line,
    cancel_order,
    confirm_order,
    pick_up_order,
    return_line,
)


class RentalOrderViewSet(TenantScopedModelViewSet):
    queryset = RentalOrder.objects.prefetch_related("lines").all()
    serializer_class = RentalOrderSerializer
    filterset_fields = ["status"]

    @action(detail=True, methods=["post"], url_path="lines")
    def add_line(self, request, pk=None):
        order = self.get_object()
        data = request.data
        try:
            product = Product.objects.get(pk=data.get("product"), tenant_id=order.tenant_id)
            warehouse = Warehouse.objects.get(pk=data.get("warehouse"), tenant_id=order.tenant_id)
        except (Product.DoesNotExist, Warehouse.DoesNotExist):
            raise ValidationError("product or warehouse not found.")

        # DRF's own DateField, not the raw string — a date arithmetic
        # property (rental_days etc.) accessed before any DB round-trip
        # would otherwise crash subtracting two strings (same class of bug
        # as the Appointments datetime fix earlier this session).
        date_field = serializers.DateField()
        line = add_rental_line(
            order,
            product=product,
            warehouse=warehouse,
            quantity=int(data.get("quantity", 1)),
            start_date=date_field.to_internal_value(data.get("start_date")),
            end_date=date_field.to_internal_value(data.get("end_date")),
            daily_rate=data.get("daily_rate"),
            late_fee_per_day=data.get("late_fee_per_day", 0),
        )
        return Response(RentalOrderLineSerializer(line).data, status=201)

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        order = confirm_order(self.get_object())
        return Response(RentalOrderSerializer(order).data)

    @action(detail=True, methods=["post"], url_path="pick-up")
    def pick_up(self, request, pk=None):
        order = pick_up_order(self.get_object())
        return Response(RentalOrderSerializer(order).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        order = cancel_order(self.get_object())
        return Response(RentalOrderSerializer(order).data)


class RentalOrderLineViewSet(TenantScopedModelViewSet):
    queryset = RentalOrderLine.objects.select_related("order", "product", "warehouse").all()
    serializer_class = RentalOrderLineSerializer
    filterset_fields = ["order", "product"]

    @action(detail=True, methods=["post"], url_path="return")
    def return_item(self, request, pk=None):
        line = return_line(self.get_object(), returned_date=request.data.get("returned_date"))
        return Response(RentalOrderLineSerializer(line).data)
