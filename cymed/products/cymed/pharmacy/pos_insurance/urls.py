"""CyMed Pharmacy pos_insurance URL routes."""
from django.urls import path

from .views import (
    AdjudicationLogViewSet,
    PosSaleItemViewSet,
    PosSaleViewSet,
    PosSessionViewSet,
    PosTerminalViewSet,
)

urlpatterns = [
    path(
        "terminals/",
        PosTerminalViewSet.as_view({"get": "list", "post": "create"}),
        name="pos-terminal-list",
    ),
    path(
        "terminals/<uuid:pk>/",
        PosTerminalViewSet.as_view(
            {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
        ),
        name="pos-terminal-detail",
    ),
    path(
        "sessions/",
        PosSessionViewSet.as_view({"get": "list", "post": "create"}),
        name="pos-session-list",
    ),
    path(
        "sessions/<uuid:pk>/",
        PosSessionViewSet.as_view(
            {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
        ),
        name="pos-session-detail",
    ),
    path(
        "sessions/open/",
        PosSessionViewSet.as_view({"post": "open_session_action"}),
        name="pos-session-open",
    ),
    path(
        "sessions/<uuid:pk>/close/",
        PosSessionViewSet.as_view({"post": "close_session_action"}),
        name="pos-session-close",
    ),
    path(
        "sales/",
        PosSaleViewSet.as_view({"get": "list", "post": "create"}),
        name="pos-sale-list",
    ),
    path(
        "sales/<uuid:pk>/",
        PosSaleViewSet.as_view(
            {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
        ),
        name="pos-sale-detail",
    ),
    path(
        "sales/start/",
        PosSaleViewSet.as_view({"post": "start_sale_action"}),
        name="pos-sale-start",
    ),
    path(
        "sales/<uuid:pk>/add-item/",
        PosSaleViewSet.as_view({"post": "add_item_action"}),
        name="pos-sale-add-item",
    ),
    path(
        "sales/<uuid:pk>/request-adjudication/",
        PosSaleViewSet.as_view({"post": "request_adjudication_action"}),
        name="pos-sale-request-adjudication",
    ),
    path(
        "sales/<uuid:pk>/finalize/",
        PosSaleViewSet.as_view({"post": "finalize_sale_action"}),
        name="pos-sale-finalize",
    ),
    path(
        "sales/<uuid:pk>/void/",
        PosSaleViewSet.as_view({"post": "void_sale_action"}),
        name="pos-sale-void",
    ),
    path(
        "sale-items/",
        PosSaleItemViewSet.as_view({"get": "list", "post": "create"}),
        name="pos-sale-item-list",
    ),
    path(
        "sale-items/<uuid:pk>/",
        PosSaleItemViewSet.as_view(
            {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
        ),
        name="pos-sale-item-detail",
    ),
    path(
        "adjudication-logs/",
        AdjudicationLogViewSet.as_view({"get": "list"}),
        name="adjudication-log-list",
    ),
    path(
        "adjudication-logs/<uuid:pk>/",
        AdjudicationLogViewSet.as_view({"get": "retrieve"}),
        name="adjudication-log-detail",
    ),
]
