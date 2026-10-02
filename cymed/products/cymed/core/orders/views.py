from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from platform.api.permissions import IsAuthenticatedClinicalStaff as IsAuthenticated  # M-7: staff-role gate
from platform.api.permissions import actor

from products.cymed.core.orders.models import Order, OrderSet
from products.cymed.core.orders.serializers import (
    OrderSerializer,
    OrderSetApplySerializer,
    OrderSetSerializer,
)
from products.cymed.core.orders.services import OrderSetError, apply_order_set


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    # Read by the project-wide tenant filter (platform.api.tenancy) so it
    # matches get_queryset below instead of narrowing it to the owner only.
    tenant_scope_fields = ("tenant_id", "fulfilling_tenant_id")
    permission_classes = [IsAuthenticated]
    # Real consumer: Phase 9's mobile e-Rx screen filters on order_type=medication.
    filterset_fields = ["order_type", "status", "priority"]

    def get_queryset(self):
        tenant_id = getattr(self.request, "tenant_id", None)
        if not tenant_id:
            return self.queryset.none()
        # CyID ecosystem, Phase 5 — the source tenant (who wrote the
        # order) and the fulfilling tenant (who executes it, e.g. an
        # external pharmacy) both see it — a real cross-tenant order
        # queue, same pattern as Consent.granted_to_tenant_id.
        return self.queryset.filter(Q(tenant_id=tenant_id) | Q(fulfilling_tenant_id=tenant_id))


class OrderSetViewSet(viewsets.ModelViewSet):
    queryset = OrderSet.objects.prefetch_related("items")
    serializer_class = OrderSetSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["is_active", "specialty"]

    def perform_create(self, serializer):
        serializer.save(tenant_id=self.request.tenant_id)

    @action(detail=True, methods=["post"])
    def apply(self, request, pk=None):
        """Order the set (or a ticked subset) for a patient."""
        order_set = self.get_object()
        if not order_set.is_active:
            return Response({"detail": "Order set is inactive."}, status=status.HTTP_400_BAD_REQUEST)
        ser = OrderSetApplySerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        try:
            orders = apply_order_set(
                order_set, tenant_id=request.tenant_id, patient_id=data["patient"],
                encounter_id=data.get("encounter"), item_ids=data.get("item_ids"),
                ordered_by=actor(request),
            )
        except OrderSetError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(OrderSerializer(orders, many=True).data, status=status.HTTP_201_CREATED)
