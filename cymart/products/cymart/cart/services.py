import uuid
from decimal import Decimal

from django.db import transaction

from products.cymart.orders.services import OrderService

from .models import Cart, CartItem, CartStatus


class DifferentStoreInCartError(Exception):
    """Raised when adding an item from a store other than the cart's
    current store — carts are single-merchant for now (master spec
    section 15), not silently merged or auto-split."""


class EmptyCartCheckoutError(Exception):
    pass


class CartAlreadyCheckedOutError(Exception):
    pass


class CartService:
    def get_or_create_active_cart(self, customer_id: uuid.UUID) -> Cart:
        cart = Cart.objects.filter(customer_id=customer_id, status=CartStatus.ACTIVE).first()
        if cart is not None:
            return cart
        return Cart.objects.create(customer_id=customer_id)

    def add_item(
        self,
        cart: Cart,
        store_id: uuid.UUID,
        tenant_id: uuid.UUID,
        product_id: uuid.UUID,
        quantity: Decimal,
        unit_price: Decimal,
        product_name: str = "",
        item_discount: Decimal = Decimal("0"),
        notes: str = "",
    ) -> CartItem:
        if cart.status != CartStatus.ACTIVE:
            raise CartAlreadyCheckedOutError(f"Cart {cart.id} is '{cart.status}', not active.")

        if cart.store_id is not None and cart.store_id != store_id:
            raise DifferentStoreInCartError(
                f"Cart {cart.id} already has items from store {cart.store_id}. "
                "Start a new cart to order from a different store."
            )

        with transaction.atomic():
            if cart.store_id is None:
                cart.store_id = store_id
                cart.tenant_id = tenant_id
                cart.save(update_fields=["store_id", "tenant_id", "updated_at"])

            item, created = CartItem.objects.get_or_create(
                cart=cart,
                product_id=product_id,
                defaults={
                    "product_name_snapshot": product_name,
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "item_discount": item_discount,
                    "notes": notes,
                },
            )
            if not created:
                item.quantity += quantity
                item.save(update_fields=["quantity"])
        return item

    def remove_item(self, cart: Cart, product_id: uuid.UUID) -> None:
        CartItem.objects.filter(cart=cart, product_id=product_id).delete()

    def checkout(
        self,
        cart: Cart,
        fulfillment_type: str = "pickup",
        delivery_fee: Decimal = Decimal("0"),
        tip_amount: Decimal = Decimal("0"),
        tax_amount: Decimal = Decimal("0"),
        cybercom_funded_discount: Decimal = Decimal("0"),
        customer_notes: str = "",
    ):
        if cart.status == CartStatus.CHECKED_OUT:
            raise CartAlreadyCheckedOutError(f"Cart {cart.id} was already checked out.")
        if cart.is_empty:
            raise EmptyCartCheckoutError(f"Cart {cart.id} has no items.")

        line_items = [
            {
                "product_id": item.product_id,
                "product_name": item.product_name_snapshot,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "item_discount": item.item_discount,
                "notes": item.notes,
            }
            for item in cart.items.all()
        ]

        # Idempotency key is derived from the cart id, not randomly minted —
        # if checkout is retried (e.g. a client timeout + client-side retry)
        # for the same cart, OrderService.create_order returns the same
        # order instead of creating a second one for the same cart.
        idempotency_key = f"cart-checkout-{cart.id}"

        order, _created = OrderService().create_order(
            idempotency_key=idempotency_key,
            tenant_id=cart.tenant_id,
            store_id=cart.store_id,
            customer_id=cart.customer_id,
            line_items=line_items,
            fulfillment_type=fulfillment_type,
            delivery_fee=delivery_fee,
            tip_amount=tip_amount,
            tax_amount=tax_amount,
            cybercom_funded_discount=cybercom_funded_discount,
            customer_notes=customer_notes,
        )

        cart.status = CartStatus.CHECKED_OUT
        cart.order_id = order.id
        cart.save(update_fields=["status", "order_id", "updated_at"])
        return order
