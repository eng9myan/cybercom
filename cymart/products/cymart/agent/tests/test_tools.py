import uuid
from decimal import Decimal

import pytest

from products.cymart.agent.tools import ALLOWED_TOOLS, OutOfScopeToolError, execute_tool
from products.cymart.dietshield.models import NutritionFact
from products.cymart.merchants.models import Merchant, Product
from products.cymart.orders.models import MarketplaceOrder


def _merchant_with_product(product_name, merchant_name="Test Diner", kind="restaurant", price="4.50"):
    merchant = Merchant.objects.create(
        name=merchant_name, kind=kind, lat=Decimal("31.95"), lng=Decimal("35.91"),
    )
    return Product.objects.create(merchant=merchant, name=product_name, price=Decimal(price))


@pytest.mark.django_db
class TestToolGate:
    def test_unknown_tool_is_refused(self):
        with pytest.raises(OutOfScopeToolError):
            execute_tool("web_search", uuid.uuid4(), query="anything")

    def test_web_search_and_email_are_not_registered_tools(self):
        # The real boundary: these simply don't exist to be called.
        assert "web_search" not in ALLOWED_TOOLS
        assert "send_email" not in ALLOWED_TOOLS
        assert "browse" not in ALLOWED_TOOLS
        assert "execute_code" not in ALLOWED_TOOLS

    def test_search_catalog_matches_by_name(self):
        # A distinctive name that won't collide with the seeded catalog
        # (25 real restaurants + 3 hypermarkets are always present).
        _merchant_with_product("Zzyzx Flame-Grilled Chicken Bowl")
        result = execute_tool("search_catalog", uuid.uuid4(), query="zzyzx")
        assert len(result["results"]) == 1
        assert result["results"][0]["name"] == "Zzyzx Flame-Grilled Chicken Bowl"
        assert "store_id" in result["results"][0] and "tenant_id" in result["results"][0]

    def test_search_catalog_filters_by_kind(self):
        _merchant_with_product("Milk 1L", merchant_name="HyperMax", kind="hypermarket")
        _merchant_with_product("Burger", merchant_name="Diner", kind="restaurant")
        result = execute_tool("search_catalog", uuid.uuid4(), query="", kind="hypermarket")
        assert all(r["merchant_kind"] == "hypermarket" for r in result["results"])

    def test_view_cart_is_scoped_to_caller(self):
        customer_id = uuid.uuid4()
        result = execute_tool("view_cart", customer_id)
        assert result["items"] == []

    def test_view_cart_status_is_plain_string_not_enum_repr(self):
        # Regression: cart.status is a Django TextChoices member fresh off
        # .create() (not yet DB-round-tripped), and Python's default dict
        # repr calls repr() on values, not str() — without an explicit
        # str() cast this leaked "CartStatus.ACTIVE" through the agent's
        # tool output instead of "active" (caught live in the frontend).
        result = execute_tool("view_cart", uuid.uuid4())
        assert result["status"] == "active"
        assert "CartStatus" not in result["status"]

    def test_order_status_hides_other_customers_orders(self):
        owner = uuid.uuid4()
        stranger = uuid.uuid4()
        order = MarketplaceOrder.objects.create(
            idempotency_key=str(uuid.uuid4()),
            tenant_id=uuid.uuid4(), store_id=uuid.uuid4(), customer_id=owner,
            subtotal=Decimal("10.00"), total_amount=Decimal("10.00"),
        )
        as_owner = execute_tool("order_status", owner, order_id=str(order.id))
        as_stranger = execute_tool("order_status", stranger, order_id=str(order.id))
        assert as_owner["found"] is True
        assert as_owner["status"] == "draft"
        assert as_stranger["found"] is False

    def test_diet_plan_status_no_profile(self):
        result = execute_tool("diet_plan_status", uuid.uuid4())
        assert result == {"has_plan": False}

    def test_replenish_basket_empty_for_new_customer(self):
        result = execute_tool("replenish_basket", uuid.uuid4())
        assert result == {"items": []}

    def test_explode_recipe_returns_matched_and_unmatched(self):
        result = execute_tool("explode_recipe", uuid.uuid4(), codes=["shakshuka"])
        assert "matched" in result and "unmatched" in result
