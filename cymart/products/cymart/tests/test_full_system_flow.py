"""The full-stack proof: a customer orders food from one real seeded
restaurant AND groceries from a real seeded hypermarket, checks both
out, one driver is batched to cover both pickups, and both orders track
independently through to delivery. Exercises merchants (real catalog) +
cart + dietshield (pass-through, no profile) + orders + pantry
(auto-logged purchases) + delivery (batched dispatch + tracking) as one
real flow, not isolated units."""

import uuid
from decimal import Decimal

import pytest

from products.cymart.cart.services import CartService
from products.cymart.delivery.models import AssignmentStatus, DeliveryRunStatus, Driver
from products.cymart.delivery.services import DispatchService, TrackingService
from products.cymart.merchants.models import Merchant
from products.cymart.pantry.models import PurchaseHistory


@pytest.mark.django_db
class TestFullOrderToDeliveryFlow:
    def test_food_and_grocery_order_one_driver_one_trip(self):
        customer_id = uuid.uuid4()

        # 1. Real seeded merchants — no fixtures invented for this test.
        restaurant = Merchant.objects.get(name="McDonald's")
        hypermarket = Merchant.objects.get(name="HyperMax")
        burger = restaurant.products.get(name="Big Mac")
        milk = hypermarket.products.filter(category="Dairy & Eggs").first()
        assert milk is not None

        # 2. Two carts — cart is single-merchant by design, so food and
        # groceries are two separate orders even though they're placed
        # together by the same customer.
        cart_svc = CartService()
        food_cart = cart_svc.get_or_create_active_cart(customer_id)
        cart_svc.add_item(
            food_cart, store_id=restaurant.id, tenant_id=restaurant.tenant_id,
            product_id=burger.id, quantity=Decimal("1"), unit_price=burger.price,
            product_name=burger.name,
        )
        food_order = cart_svc.checkout(food_cart, fulfillment_type="delivery")

        grocery_cart = cart_svc.get_or_create_active_cart(customer_id)
        cart_svc.add_item(
            grocery_cart, store_id=hypermarket.id, tenant_id=hypermarket.tenant_id,
            product_id=milk.id, quantity=Decimal("2"), unit_price=milk.price,
            product_name=milk.name,
        )
        grocery_order = cart_svc.checkout(grocery_cart, fulfillment_type="delivery")

        assert food_order.customer_id == grocery_order.customer_id == customer_id

        # 3. Checkout auto-fed the pantry's replenish engine for the
        # grocery line (see cart.services.CartService.checkout).
        assert PurchaseHistory.objects.filter(
            customer_id=customer_id, product_id=milk.id
        ).exists()

        # 4. One online driver near both pickup points.
        Driver.objects.create(
            name="Ahmad", phone="+962790000000",
            current_lat=restaurant.lat, current_lng=restaurant.lng, is_online=True,
        )

        # 5. Batch-dispatch — one driver, two pickups, not two couriers.
        run = DispatchService().assign_batch([
            (food_order, restaurant.lat, restaurant.lng),
            (grocery_order, hypermarket.lat, hypermarket.lng),
        ])
        assert run.assignments.count() == 2
        assert len({a.driver_id for a in run.assignments.all()}) == 1

        # 6. Driver works the trip: picks up food, picks up groceries,
        # delivers both. Each order's own tracking stays independent.
        tracking = TrackingService()
        food_leg = run.assignments.get(order=food_order)
        grocery_leg = run.assignments.get(order=grocery_order)

        tracking.record_event(food_leg, AssignmentStatus.PICKED_UP, note="Left McDonald's")
        tracking.record_event(grocery_leg, AssignmentStatus.PICKED_UP, note="Left HyperMax")

        food_status = tracking.status_for_order(food_order)
        assert food_status["status"] == AssignmentStatus.PICKED_UP
        assert food_status["run_id"] == run.id

        tracking.record_event(food_leg, AssignmentStatus.DELIVERED, note="Handed to customer")
        run.refresh_from_db()
        assert run.status == DeliveryRunStatus.ACTIVE  # groceries still out

        tracking.record_event(grocery_leg, AssignmentStatus.DELIVERED, note="Handed to customer")
        run.refresh_from_db()
        assert run.status == DeliveryRunStatus.COMPLETED

        # 7. Both orders show fully delivered, independently trackable.
        assert tracking.status_for_order(food_order)["status"] == AssignmentStatus.DELIVERED
        assert tracking.status_for_order(grocery_order)["status"] == AssignmentStatus.DELIVERED
