"""Explicit URL routes for the DTC test catalog sub-app."""
from __future__ import annotations

from django.urls import path

from .views import (
    DtcCategoryViewSet,
    DtcKitViewSet,
    DtcOrderViewSet,
    DtcProductViewSet,
)

urlpatterns = [
    path(
        "categories/",
        DtcCategoryViewSet.as_view({"get": "list", "post": "create"}),
        name="dtc-category-list",
    ),
    path(
        "categories/<uuid:pk>/",
        DtcCategoryViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="dtc-category-detail",
    ),
    path(
        "products/",
        DtcProductViewSet.as_view({"get": "list", "post": "create"}),
        name="dtc-product-list",
    ),
    path(
        "products/<uuid:pk>/",
        DtcProductViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="dtc-product-detail",
    ),
    path(
        "kits/",
        DtcKitViewSet.as_view({"get": "list", "post": "create"}),
        name="dtc-kit-list",
    ),
    path(
        "kits/<uuid:pk>/",
        DtcKitViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="dtc-kit-detail",
    ),
    path(
        "orders/",
        DtcOrderViewSet.as_view({"get": "list", "post": "create"}),
        name="dtc-order-list",
    ),
    path(
        "orders/<uuid:pk>/",
        DtcOrderViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="dtc-order-detail",
    ),
    path(
        "orders/place/",
        DtcOrderViewSet.as_view({"post": "place"}),
        name="dtc-order-place",
    ),
    path(
        "orders/<uuid:pk>/dispatch-kit/",
        DtcOrderViewSet.as_view({"post": "dispatch_kit"}),
        name="dtc-order-dispatch-kit",
    ),
    path(
        "orders/activate-kit/",
        DtcOrderViewSet.as_view({"post": "activate_kit"}),
        name="dtc-order-activate-kit",
    ),
    path(
        "orders/<uuid:pk>/sample-received/",
        DtcOrderViewSet.as_view({"post": "sample_received"}),
        name="dtc-order-sample-received",
    ),
    path(
        "orders/<uuid:pk>/mark-results-ready/",
        DtcOrderViewSet.as_view({"post": "mark_results_ready"}),
        name="dtc-order-mark-results-ready",
    ),
    path(
        "orders/<uuid:pk>/schedule-consultation/",
        DtcOrderViewSet.as_view({"post": "schedule_consultation"}),
        name="dtc-order-schedule-consultation",
    ),
    path(
        "orders/<uuid:pk>/cancel/",
        DtcOrderViewSet.as_view({"post": "cancel"}),
        name="dtc-order-cancel",
    ),
]
