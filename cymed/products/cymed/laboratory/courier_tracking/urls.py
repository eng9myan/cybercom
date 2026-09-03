"""URL routes for CyMed Laboratory courier tracking."""

from __future__ import annotations

from django.urls import path

from .views import (
    ChainOfCustodyEventViewSet,
    ManifestViewSet,
    RouteViewSet,
    RunViewSet,
    TransportTemperatureViewSet,
)


route_list = RouteViewSet.as_view({"get": "list", "post": "create"})
route_detail = RouteViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)

run_list = RunViewSet.as_view({"get": "list", "post": "create"})
run_detail = RunViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)
run_open = RunViewSet.as_view({"post": "open_run"})
run_close = RunViewSet.as_view({"post": "close_run"})
run_generate_manifest = RunViewSet.as_view({"post": "generate_manifest"})

coc_list = ChainOfCustodyEventViewSet.as_view({"get": "list", "post": "create"})
coc_detail = ChainOfCustodyEventViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)
coc_record = ChainOfCustodyEventViewSet.as_view({"post": "record"})
coc_locate = ChainOfCustodyEventViewSet.as_view({"get": "locate"})

temp_list = TransportTemperatureViewSet.as_view({"get": "list", "post": "create"})
temp_detail = TransportTemperatureViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)
temp_record = TransportTemperatureViewSet.as_view({"post": "record"})

manifest_list = ManifestViewSet.as_view({"get": "list", "post": "create"})
manifest_detail = ManifestViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)
manifest_deliver = ManifestViewSet.as_view({"post": "deliver"})


urlpatterns = [
    path("routes/", route_list, name="cymed-lab-courier-route-list"),
    path("routes/<uuid:pk>/", route_detail, name="cymed-lab-courier-route-detail"),
    path("runs/", run_list, name="cymed-lab-courier-run-list"),
    path("runs/<uuid:pk>/", run_detail, name="cymed-lab-courier-run-detail"),
    path("runs/open/", run_open, name="cymed-lab-courier-run-open"),
    path("runs/<uuid:pk>/close/", run_close, name="cymed-lab-courier-run-close"),
    path(
        "runs/<uuid:pk>/generate-manifest/",
        run_generate_manifest,
        name="cymed-lab-courier-run-generate-manifest",
    ),
    path("custody-events/", coc_list, name="cymed-lab-courier-coc-list"),
    path("custody-events/<uuid:pk>/", coc_detail, name="cymed-lab-courier-coc-detail"),
    path("custody-events/record/", coc_record, name="cymed-lab-courier-coc-record"),
    path("custody-events/locate/", coc_locate, name="cymed-lab-courier-coc-locate"),
    path("temperatures/", temp_list, name="cymed-lab-courier-temp-list"),
    path("temperatures/<uuid:pk>/", temp_detail, name="cymed-lab-courier-temp-detail"),
    path("temperatures/record/", temp_record, name="cymed-lab-courier-temp-record"),
    path("manifests/", manifest_list, name="cymed-lab-courier-manifest-list"),
    path("manifests/<uuid:pk>/", manifest_detail, name="cymed-lab-courier-manifest-detail"),
    path(
        "manifests/<uuid:pk>/deliver/",
        manifest_deliver,
        name="cymed-lab-courier-manifest-deliver",
    ),
]
