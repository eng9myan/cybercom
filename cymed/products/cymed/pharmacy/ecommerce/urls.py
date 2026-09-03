"""CyMed Pharmacy E-commerce URL routes."""
from django.urls import path

from .views import (
    CartItemViewSet,
    CartViewSet,
    PharmacyOrderItemViewSet,
    PharmacyOrderViewSet,
    PharmacyProductViewSet,
    RefillRequestViewSet,
)

urlpatterns = [
    path(
        "products/",
        PharmacyProductViewSet.as_view({"get": "list", "post": "create"}),
        name="cymed-pharmacy-ecommerce-product-list",
    ),
    path(
        "products/<uuid:pk>/",
        PharmacyProductViewSet.as_view(
            {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
        ),
        name="cymed-pharmacy-ecommerce-product-detail",
    ),
    path(
        "refill-requests/",
        RefillRequestViewSet.as_view({"get": "list", "post": "create"}),
        name="cymed-pharmacy-ecommerce-refill-list",
    ),
    path(
        "refill-requests/<uuid:pk>/",
        RefillRequestViewSet.as_view(
            {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
        ),
        name="cymed-pharmacy-ecommerce-refill-detail",
    ),
    path(
        "refill-requests/submit/",
        RefillRequestViewSet.as_view({"post": "submit"}),
        name="cymed-pharmacy-ecommerce-refill-submit",
    ),
    path(
        "refill-requests/<uuid:pk>/verify/",
        RefillRequestViewSet.as_view({"post": "verify"}),
        name="cymed-pharmacy-ecommerce-refill-verify",
    ),
    path(
        "carts/",
        CartViewSet.as_view({"get": "list", "post": "create"}),
        name="cymed-pharmacy-ecommerce-cart-list",
    ),
    path(
        "carts/<uuid:pk>/",
        CartViewSet.as_view(
            {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
        ),
        name="cymed-pharmacy-ecommerce-cart-detail",
    ),
    path(
        "carts/add-item/",
        CartViewSet.as_view({"post": "add_item"}),
        name="cymed-pharmacy-ecommerce-cart-add-item",
    ),
    path(
        "carts/<uuid:pk>/checkout/",
        CartViewSet.as_view({"post": "checkout"}),
        name="cymed-pharmacy-ecommerce-cart-checkout",
    ),
    path(
        "cart-items/",
        CartItemViewSet.as_view({"get": "list", "post": "create"}),
        name="cymed-pharmacy-ecommerce-cart-item-list",
    ),
    path(
        "cart-items/<uuid:pk>/",
        CartItemViewSet.as_view(
            {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
        ),
        name="cymed-pharmacy-ecommerce-cart-item-detail",
    ),
    path(
        "orders/",
        PharmacyOrderViewSet.as_view({"get": "list", "post": "create"}),
        name="cymed-pharmacy-ecommerce-order-list",
    ),
    path(
        "orders/<uuid:pk>/",
        PharmacyOrderViewSet.as_view(
            {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
        ),
        name="cymed-pharmacy-ecommerce-order-detail",
    ),
    path(
        "orders/<uuid:pk>/mark-ready/",
        PharmacyOrderViewSet.as_view({"post": "mark_ready"}),
        name="cymed-pharmacy-ecommerce-order-mark-ready",
    ),
    path(
        "orders/<uuid:pk>/mark-shipped/",
        PharmacyOrderViewSet.as_view({"post": "mark_shipped"}),
        name="cymed-pharmacy-ecommerce-order-mark-shipped",
    ),
    path(
        "orders/<uuid:pk>/mark-delivered/",
        PharmacyOrderViewSet.as_view({"post": "mark_delivered"}),
        name="cymed-pharmacy-ecommerce-order-mark-delivered",
    ),
    path(
        "order-items/",
        PharmacyOrderItemViewSet.as_view({"get": "list", "post": "create"}),
        name="cymed-pharmacy-ecommerce-order-item-list",
    ),
    path(
        "order-items/<uuid:pk>/",
        PharmacyOrderItemViewSet.as_view(
            {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
        ),
        name="cymed-pharmacy-ecommerce-order-item-detail",
    ),
]
