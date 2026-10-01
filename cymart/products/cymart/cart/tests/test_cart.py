import uuid
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from products.cymart.cart.models import Cart, CartStatus
from products.cymart.cart.services import (
    CartAlreadyCheckedOutError,
    CartService,
    DietPlanViolationError,
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


@pytest.mark.django_db
class TestCartDietShieldGate:
    """The shield is a no-op for any customer without a DietProfile — that
    presence is the single on/off switch (see products.cymart.dietshield).
    These prove the cart hook actually calls the gate."""

    def _keto_profile(self, customer_id):
        from decimal import Decimal as D

        from products.cymart.dietshield.models import (
            ActivityLevel, DietProfile, DietRegime, GoalType, Sex, Strictness,
        )
        from products.cymart.dietshield.plan_builder import PlanBuilder

        profile = DietProfile.objects.create(
            customer_id=customer_id, sex=Sex.MALE, age=40, height_cm=D("180"),
            weight_kg=D("90"), activity_level=ActivityLevel.MODERATE,
            goal_type=GoalType.MAINTAIN, strictness=Strictness.STRICT,
        )
        keto, _ = DietRegime.objects.get_or_create(
            code="keto", defaults={"name_en": "Keto", "max_item_carbs_g": D("15")}
        )
        profile.regimes.add(keto)
        PlanBuilder().build(profile)
        return profile

    def test_customer_without_diet_profile_is_unaffected(self):
        cart = Cart.objects.create(customer_id=uuid.uuid4())
        item = CartService().add_item(
            cart, uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), Decimal("1"), Decimal("10.00")
        )
        assert item is not None

    def test_off_plan_item_blocked_for_shield_customer(self):
        from decimal import Decimal as D

        from products.cymart.dietshield.models import NutritionFact

        customer_id = uuid.uuid4()
        self._keto_profile(customer_id)
        cart = Cart.objects.create(customer_id=customer_id)
        off_plan_product = uuid.uuid4()
        NutritionFact.objects.create(
            product_id=off_plan_product, calories=D("820"), carbs_g=D("82"),
            ingredients=["wheat", "cream"],
        )
        with pytest.raises(DietPlanViolationError):
            CartService().add_item(
                cart, uuid.uuid4(), uuid.uuid4(), off_plan_product, Decimal("1"), Decimal("12.00")
            )
        assert cart.items.count() == 0

    def test_on_plan_item_allowed_for_shield_customer(self):
        from decimal import Decimal as D

        from products.cymart.dietshield.models import NutritionFact

        customer_id = uuid.uuid4()
        self._keto_profile(customer_id)
        cart = Cart.objects.create(customer_id=customer_id)
        good_product = uuid.uuid4()
        NutritionFact.objects.create(
            product_id=good_product, calories=D("480"), carbs_g=D("6"),
            diet_tags=["keto"], ingredients=["chicken"],
        )
        item = CartService().add_item(
            cart, uuid.uuid4(), uuid.uuid4(), good_product, Decimal("1"), Decimal("12.00")
        )
        assert item is not None
        assert cart.items.count() == 1


@pytest.mark.django_db
class TestActiveCartEndpoint:
    """The mobile app needs to discover 'my current cart' without already
    knowing its id — /carts/active/ derives customer_id from the verified
    JWT (user_session), not a client-supplied param."""

    def _authed_client(self, mint_token, mock_jwks, user_id):
        client = APIClient()
        token = mint_token({"sub": str(user_id), "roles": ["customer"], "permissions": []})
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return client

    def test_active_creates_cart_on_first_call(self, mint_token, mock_jwks):
        user_id = uuid.uuid4()
        client = self._authed_client(mint_token, mock_jwks, user_id)
        resp = client.get("/api/v1/marketplace/carts/active/")
        assert resp.status_code == 200, resp.content
        assert resp.json()["customer_id"] == str(user_id)
        assert resp.json()["status"] == CartStatus.ACTIVE

    def test_active_returns_same_cart_on_second_call(self, mint_token, mock_jwks):
        user_id = uuid.uuid4()
        client = self._authed_client(mint_token, mock_jwks, user_id)
        first = client.get("/api/v1/marketplace/carts/active/").json()
        second = client.get("/api/v1/marketplace/carts/active/").json()
        assert first["id"] == second["id"]

    def test_active_cannot_be_spoofed_via_query_param(self, mint_token, mock_jwks):
        real_user_id = uuid.uuid4()
        other_user_id = uuid.uuid4()
        client = self._authed_client(mint_token, mock_jwks, real_user_id)
        resp = client.get(f"/api/v1/marketplace/carts/active/?customer_id={other_user_id}")
        assert resp.json()["customer_id"] == str(real_user_id)
