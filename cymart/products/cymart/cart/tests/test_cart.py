import uuid
from decimal import Decimal

import pytest

from products.cymart.cart.models import Cart, CartStatus
from products.cymart.cart.services import (
    CartAlreadyCheckedOutError,
    CartService,
    DifferentStoreInCartError,
    EmptyCartCheckoutError,
)
from products.cymart.orders.models import MarketplaceOrderStatus


@pytest.mark.django_db
class TestCartService:
    def test_get_or_create_active_cart_reuses_existing(self):
        customer_id = uuid.uuid4()
        svc = CartService()
        cart1 = svc.get_or_create_active_cart(customer_id)
        cart2 = svc.get_or_create_active_cart(customer_id)
        assert cart1.id == cart2.id

    def test_add_item_sets_cart_store(self):
        cart = Cart.objects.create(customer_id=uuid.uuid4())
        store_id, tenant_id = uuid.uuid4(), uuid.uuid4()
        CartService().add_item(
            cart, store_id=store_id, tenant_id=tenant_id, product_id=uuid.uuid4(),
            quantity=Decimal("1"), unit_price=Decimal("10.00"),
        )
        cart.refresh_from_db()
        assert cart.store_id == store_id
        assert cart.tenant_id == tenant_id

    def test_adding_same_product_twice_merges_quantity(self):
        cart = Cart.objects.create(customer_id=uuid.uuid4())
        store_id, tenant_id = uuid.uuid4(), uuid.uuid4()
        product_id = uuid.uuid4()
        svc = CartService()
        svc.add_item(cart, store_id, tenant_id, product_id, Decimal("1"), Decimal("10.00"))
        svc.add_item(cart, store_id, tenant_id, product_id, Decimal("2"), Decimal("10.00"))
        assert cart.items.count() == 1
        assert cart.items.first().quantity == Decimal("3")

    def test_adding_item_from_different_store_raises(self):
        cart = Cart.objects.create(customer_id=uuid.uuid4())
        tenant_id = uuid.uuid4()
        svc = CartService()
        svc.add_item(cart, uuid.uuid4(), tenant_id, uuid.uuid4(), Decimal("1"), Decimal("10.00"))
        with pytest.raises(DifferentStoreInCartError):
            svc.add_item(cart, uuid.uuid4(), tenant_id, uuid.uuid4(), Decimal("1"), Decimal("5.00"))

    def test_checkout_empty_cart_raises(self):
        cart = Cart.objects.create(customer_id=uuid.uuid4())
        with pytest.raises(EmptyCartCheckoutError):
            CartService().checkout(cart)

    def test_checkout_creates_marketplace_order(self):
        cart = Cart.objects.create(customer_id=uuid.uuid4())
        svc = CartService()
        svc.add_item(
            cart, uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), Decimal("2"), Decimal("25.00")
        )
        order = svc.checkout(cart)
        cart.refresh_from_db()
        assert cart.status == CartStatus.CHECKED_OUT
        assert cart.order_id == order.id
        assert order.status == MarketplaceOrderStatus.DRAFT
        assert order.subtotal == Decimal("50.00")
        assert order.lines.count() == 1

    def test_checkout_twice_raises_not_duplicate_order(self):
        cart = Cart.objects.create(customer_id=uuid.uuid4())
        svc = CartService()
        svc.add_item(cart, uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), Decimal("1"), Decimal("10.00"))
        svc.checkout(cart)
        with pytest.raises(CartAlreadyCheckedOutError):
            svc.checkout(cart)

    def test_cannot_add_item_to_checked_out_cart(self):
        cart = Cart.objects.create(customer_id=uuid.uuid4())
        svc = CartService()
        svc.add_item(cart, uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), Decimal("1"), Decimal("10.00"))
        svc.checkout(cart)
        with pytest.raises(CartAlreadyCheckedOutError):
            svc.add_item(cart, cart.store_id, cart.tenant_id, uuid.uuid4(), Decimal("1"), Decimal("5.00"))
