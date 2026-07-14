from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Cart
from .serializers import CartSerializer
from .services import (
    CartAlreadyCheckedOutError,
    CartService,
    DifferentStoreInCartError,
    EmptyCartCheckoutError,
)


class CartViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]
    queryset = Cart.objects.all()

    @action(detail=False, methods=["get"])
    def active(self, request):
        """Returns the caller's active cart, creating an empty one if none
        exists yet. customer_id comes from the verified JWT (user_session),
        never a client-supplied query param — a client can't fetch or
        create a cart on another customer's behalf."""
        customer_id = request.user_session["user_id"]
        cart = CartService().get_or_create_active_cart(customer_id)
        return Response(self.get_serializer(cart).data)

    @action(detail=True, methods=["post"])
    def add_item(self, request, pk=None):
        cart = self.get_object()
        try:
            CartService().add_item(
                cart=cart,
                store_id=request.data["store_id"],
                tenant_id=request.data["tenant_id"],
                product_id=request.data["product_id"],
                quantity=request.data["quantity"],
                unit_price=request.data["unit_price"],
                product_name=request.data.get("product_name", ""),
                item_discount=request.data.get("item_discount", 0),
            )
        except (DifferentStoreInCartError, CartAlreadyCheckedOutError) as exc:
            return Response({"detail": str(exc)}, status=409)
        cart.refresh_from_db()
        return Response(self.get_serializer(cart).data)

    @action(detail=True, methods=["post"])
    def checkout(self, request, pk=None):
        cart = self.get_object()
        try:
            order = CartService().checkout(
                cart,
                fulfillment_type=request.data.get("fulfillment_type", "pickup"),
                delivery_fee=request.data.get("delivery_fee", 0),
                tip_amount=request.data.get("tip_amount", 0),
                tax_amount=request.data.get("tax_amount", 0),
            )
        except (EmptyCartCheckoutError, CartAlreadyCheckedOutError) as exc:
            return Response({"detail": str(exc)}, status=409)
        return Response({"order_id": str(order.id), "status": order.status})
