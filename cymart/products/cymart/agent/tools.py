"""The tool allowlist — the ONLY functions the CyMart agent can ever
call.

This is the real security boundary, not the system prompt. A tool the
model was never given cannot be invoked; a tool name it tries to call
that isn't in ALLOWED_TOOLS is refused in ``execute_tool`` regardless of
what the model asked for. There is no web-search, email, browser, or
code-exec tool here and there never will be — the agent can only search
CyMart's own catalog, check the diet shield, and operate the caller's
own cart/orders/pantry. Every handler takes the caller's ``customer_id``
from the verified JWT (never from the model or the request body), so the
agent can't read or act on another customer's data.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import Callable


@dataclass
class ToolSpec:
    name: str
    description: str
    parameters: dict  # JSON Schema for the tool's arguments
    handler: Callable[..., dict]


class OutOfScopeToolError(Exception):
    """Raised when a tool name outside ALLOWED_TOOLS is requested."""


# ── Handlers — each one wraps an existing, already-tested service. This
# module adds no new business logic, only a narrow, customer-scoped
# calling surface over it. ──────────────────────────────────────────────

def _search_catalog(customer_id, query: str, kind: str | None = None, limit: int = 5, **_) -> dict:
    """Searches the real seeded merchant catalog (restaurants +
    hypermarkets) by item, merchant, or category name. Returns
    everything add_to_cart needs (store_id, tenant_id, price) so the
    model can chain search -> add_to_cart without a second lookup.
    ``kind`` optionally narrows to "restaurant" or "hypermarket"."""
    from products.cymart.merchants.services import CatalogSearch

    results = CatalogSearch().search(query, kind=kind, limit=max(1, min(limit, 20)))
    return {
        "results": [
            {
                "product_id": str(r["product_id"]),
                "name": r["name"],
                "price": float(r["price"]),
                "unit": r["unit"],
                "merchant_name": r["merchant_name"],
                "merchant_kind": r["merchant_kind"],
                "store_id": str(r["store_id"]),
                "tenant_id": str(r["tenant_id"]),
            }
            for r in results
        ]
    }


def _diet_plan_status(customer_id, **_) -> dict:
    from products.cymart.dietshield.services import DietDayService, ProfileService

    svc = ProfileService()
    profile = svc.get(customer_id)
    if profile is None:
        return {"has_plan": False}
    plan = svc.active_plan(profile)
    if plan is None:
        return {"has_plan": False}
    return {"has_plan": True, **DietDayService().status(profile, plan)}


def _evaluate_items(customer_id, items: list, **_) -> dict:
    from products.cymart.dietshield.services import ShieldGate

    parsed = [
        {"product_id": uuid.UUID(str(i["product_id"])), "quantity": Decimal(str(i.get("quantity", 1)))}
        for i in items
    ]
    result = ShieldGate().evaluate_items(customer_id, parsed)
    if result is None:
        return {"shield_active": False}
    return {
        "shield_active": True,
        "overall": result.overall.name,
        "allowed": result.allowed,
        "lines": [
            {"product_id": str(ln.product_id), "severity": ln.severity.name, "reason": ln.reason}
            for ln in result.lines
        ],
    }


def _view_cart(customer_id, **_) -> dict:
    from products.cymart.cart.services import CartService

    cart = CartService().get_or_create_active_cart(customer_id)
    return {
        "cart_id": str(cart.id),
        "status": str(cart.status),
        "items": [
            {
                "product_id": str(i.product_id),
                "name": i.product_name_snapshot,
                "quantity": str(i.quantity),
                "unit_price": str(i.unit_price),
            }
            for i in cart.items.all()
        ],
    }


def _add_to_cart(
    customer_id, store_id, tenant_id, product_id, quantity, unit_price, product_name="", **_
) -> dict:
    from products.cymart.cart.services import (
        CartService,
        DietPlanViolationError,
        DifferentStoreInCartError,
    )

    cart = CartService().get_or_create_active_cart(customer_id)
    try:
        CartService().add_item(
            cart,
            store_id=uuid.UUID(str(store_id)),
            tenant_id=uuid.UUID(str(tenant_id)),
            product_id=uuid.UUID(str(product_id)),
            quantity=Decimal(str(quantity)),
            unit_price=Decimal(str(unit_price)),
            product_name=product_name,
        )
    except DietPlanViolationError as exc:
        return {"blocked": True, "reason": str(exc)}
    except DifferentStoreInCartError as exc:
        return {"blocked": True, "reason": str(exc)}
    return {"blocked": False, **_view_cart(customer_id)}


def _checkout(customer_id, fulfillment_type: str = "delivery", delivery_fee: str = "0", **_) -> dict:
    from products.cymart.cart.services import (
        CartAlreadyCheckedOutError,
        CartService,
        EmptyCartCheckoutError,
    )

    cart = CartService().get_or_create_active_cart(customer_id)
    try:
        order = CartService().checkout(
            cart, fulfillment_type=fulfillment_type, delivery_fee=Decimal(str(delivery_fee))
        )
    except (EmptyCartCheckoutError, CartAlreadyCheckedOutError) as exc:
        return {"success": False, "reason": str(exc)}
    return {"success": True, "order_id": str(order.id), "status": str(order.status)}


def _order_status(customer_id, order_id, **_) -> dict:
    from products.cymart.orders.models import MarketplaceOrder

    try:
        order = MarketplaceOrder.objects.get(id=uuid.UUID(str(order_id)), customer_id=customer_id)
    except (MarketplaceOrder.DoesNotExist, ValueError):
        # Ownership is enforced in the lookup itself — another customer's
        # order id simply isn't found, never leaked.
        return {"found": False}
    return {"found": True, "order_id": str(order.id), "status": str(order.status)}


def _explode_recipe(customer_id, codes: list, servings_map: dict | None = None, **_) -> dict:
    from products.cymart.pantry.services import GroceryListBuilder

    return GroceryListBuilder().from_recipes(codes, servings_map)


def _replenish_basket(customer_id, **_) -> dict:
    from products.cymart.pantry.services import ReplenishEngine

    return {"items": ReplenishEngine().build_refill_basket(customer_id)}


ALLOWED_TOOLS: dict[str, ToolSpec] = {
    spec.name: spec
    for spec in [
        ToolSpec(
            "search_catalog",
            "Search CyMart's restaurants and hypermarkets for a food or "
            "grocery item by name, cuisine, or store. Returns price and "
            "the store_id/tenant_id needed to add an item to the cart.",
            {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "kind": {
                        "type": "string",
                        "enum": ["restaurant", "hypermarket"],
                        "description": "Optionally narrow to restaurants or hypermarkets only.",
                    },
                    "limit": {"type": "integer", "default": 5},
                },
                "required": ["query"],
            },
            _search_catalog,
        ),
        ToolSpec(
            "diet_plan_status",
            "Get the caller's diet plan and today's remaining calorie budget.",
            {"type": "object", "properties": {}},
            _diet_plan_status,
        ),
        ToolSpec(
            "evaluate_items",
            "Check whether items fit the caller's diet plan before adding them to the cart.",
            {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "product_id": {"type": "string"},
                                "quantity": {"type": "number", "default": 1},
                            },
                            "required": ["product_id"],
                        },
                    }
                },
                "required": ["items"],
            },
            _evaluate_items,
        ),
        ToolSpec(
            "view_cart",
            "View the caller's active cart.",
            {"type": "object", "properties": {}},
            _view_cart,
        ),
        ToolSpec(
            "add_to_cart",
            "Add an item to the caller's cart. Blocked automatically if it breaks their diet plan.",
            {
                "type": "object",
                "properties": {
                    "store_id": {"type": "string"},
                    "tenant_id": {"type": "string"},
                    "product_id": {"type": "string"},
                    "quantity": {"type": "number"},
                    "unit_price": {"type": "number"},
                    "product_name": {"type": "string"},
                },
                "required": ["store_id", "tenant_id", "product_id", "quantity", "unit_price"],
            },
            _add_to_cart,
        ),
        ToolSpec(
            "checkout",
            "Check out the caller's active cart.",
            {
                "type": "object",
                "properties": {
                    "fulfillment_type": {"type": "string", "default": "delivery"},
                    "delivery_fee": {"type": "string", "default": "0"},
                },
            },
            _checkout,
        ),
        ToolSpec(
            "order_status",
            "Look up the status of one of the caller's own past orders.",
            {
                "type": "object",
                "properties": {"order_id": {"type": "string"}},
                "required": ["order_id"],
            },
            _order_status,
        ),
        ToolSpec(
            "explode_recipe",
            "Turn one or more recipe codes into a grocery list matched to real items.",
            {
                "type": "object",
                "properties": {
                    "codes": {"type": "array", "items": {"type": "string"}},
                    "servings_map": {"type": "object"},
                },
                "required": ["codes"],
            },
            _explode_recipe,
        ),
        ToolSpec(
            "replenish_basket",
            "Get grocery items the caller is predicted to be running low on.",
            {"type": "object", "properties": {}},
            _replenish_basket,
        ),
    ]
}


def execute_tool(name: str, customer_id: uuid.UUID, **kwargs) -> dict:
    """The default-deny gate. Every tool call — from any provider, real
    or fake — passes through here before it touches a service. A name
    outside ALLOWED_TOOLS is refused; nothing else is ever executed."""
    spec = ALLOWED_TOOLS.get(name)
    if spec is None:
        raise OutOfScopeToolError(f"Tool '{name}' is not available to the CyMart agent.")
    return spec.handler(customer_id, **kwargs)
