"""CyMed Pharmacy E-commerce viewsets."""
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from . import services
from .models import (
    Cart,
    CartItem,
    PharmacyOrder,
    PharmacyOrderItem,
    PharmacyProduct,
    RefillRequest,
)
from .serializers import (
    CartItemSerializer,
    CartSerializer,
    PharmacyOrderItemSerializer,
    PharmacyOrderSerializer,
    PharmacyProductSerializer,
    RefillRequestSerializer,
)


class PharmacyProductViewSet(viewsets.ModelViewSet):
    queryset = PharmacyProduct.objects.all()
    serializer_class = PharmacyProductSerializer


class RefillRequestViewSet(viewsets.ModelViewSet):
    queryset = RefillRequest.objects.all()
    serializer_class = RefillRequestSerializer

    @action(detail=False, methods=["post"], url_path="submit")
    def submit(self, request):
        data = request.data
        refill = services.submit_refill_request(
            tenant_id=data.get("tenant_id"),
            patient_profile_id=data.get("patient_profile_id"),
            drug_name=data.get("drug_name"),
            qty=int(data.get("qty", 1)),
            drug_id=data.get("drug_id"),
            original_prescription_id=data.get("original_prescription_id"),
            delivery_address=data.get("delivery_address"),
        )
        return Response(self.get_serializer(refill).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="verify")
    def verify(self, request, pk=None):
        data = request.data
        refill = services.verify_refill(
            refill_id=pk,
            approved=bool(data.get("approved", True)),
            pharmacist_notes=data.get("pharmacist_notes", ""),
        )
        return Response(self.get_serializer(refill).data)


class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer

    @action(detail=False, methods=["post"], url_path="add-item")
    def add_item(self, request):
        data = request.data
        item = services.add_to_cart(
            tenant_id=data.get("tenant_id"),
            patient_profile_id=data.get("patient_profile_id"),
            product_id=data.get("product_id"),
            qty=int(data.get("qty", 1)),
        )
        return Response(CartItemSerializer(item).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="checkout")
    def checkout(self, request, pk=None):
        data = request.data
        slot = None
        if data.get("delivery_slot_start") and data.get("delivery_slot_end"):
            slot = (data.get("delivery_slot_start"), data.get("delivery_slot_end"))
        order = services.checkout_cart(
            cart_id=pk,
            fulfillment=data.get("fulfillment", "pickup"),
            delivery_address=data.get("delivery_address"),
            delivery_slot=slot,
        )
        return Response(PharmacyOrderSerializer(order).data, status=status.HTTP_201_CREATED)


class CartItemViewSet(viewsets.ModelViewSet):
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer


class PharmacyOrderViewSet(viewsets.ModelViewSet):
    queryset = PharmacyOrder.objects.all()
    serializer_class = PharmacyOrderSerializer

    @action(detail=True, methods=["post"], url_path="mark-ready")
    def mark_ready(self, request, pk=None):
        order = services.mark_ready(pk)
        return Response(self.get_serializer(order).data)

    @action(detail=True, methods=["post"], url_path="mark-shipped")
    def mark_shipped(self, request, pk=None):
        order = services.mark_shipped(pk, delivery_id=request.data.get("delivery_id"))
        return Response(self.get_serializer(order).data)

    @action(detail=True, methods=["post"], url_path="mark-delivered")
    def mark_delivered(self, request, pk=None):
        order = services.mark_delivered(pk)
        return Response(self.get_serializer(order).data)


class PharmacyOrderItemViewSet(viewsets.ModelViewSet):
    queryset = PharmacyOrderItem.objects.all()
    serializer_class = PharmacyOrderItemSerializer
