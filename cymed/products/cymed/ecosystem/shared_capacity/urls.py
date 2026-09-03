"""URL routes for CyMed shared capacity marketplace and pools."""
from __future__ import annotations

from django.urls import path

from .views import (
    RadiologistPoolShiftViewSet,
    ResourceMatchViewSet,
    ResourceOfferViewSet,
    ResourceRequestViewSet,
)

offer_list = ResourceOfferViewSet.as_view({"get": "list", "post": "create"})
offer_detail = ResourceOfferViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)
offer_post = ResourceOfferViewSet.as_view({"post": "post_offer"})

request_list = ResourceRequestViewSet.as_view({"get": "list", "post": "create"})
request_detail = ResourceRequestViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)
request_post = ResourceRequestViewSet.as_view({"post": "post_request"})
request_match = ResourceRequestViewSet.as_view({"post": "match"})

match_list = ResourceMatchViewSet.as_view({"get": "list", "post": "create"})
match_detail = ResourceMatchViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)
match_accept = ResourceMatchViewSet.as_view({"post": "accept"})
match_decline = ResourceMatchViewSet.as_view({"post": "decline"})
match_fulfill = ResourceMatchViewSet.as_view({"post": "fulfill"})

shift_list = RadiologistPoolShiftViewSet.as_view({"get": "list", "post": "create"})
shift_detail = RadiologistPoolShiftViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)
shift_post = RadiologistPoolShiftViewSet.as_view({"post": "post_shift"})
shift_increment = RadiologistPoolShiftViewSet.as_view({"post": "increment_load"})


urlpatterns = [
    path("offers/", offer_list, name="shared-capacity-offer-list"),
    path("offers/post-offer/", offer_post, name="shared-capacity-offer-post"),
    path("offers/<uuid:pk>/", offer_detail, name="shared-capacity-offer-detail"),
    path("requests/", request_list, name="shared-capacity-request-list"),
    path("requests/post-request/", request_post, name="shared-capacity-request-post"),
    path("requests/<uuid:pk>/", request_detail, name="shared-capacity-request-detail"),
    path("requests/<uuid:pk>/match/", request_match, name="shared-capacity-request-match"),
    path("matches/", match_list, name="shared-capacity-match-list"),
    path("matches/<uuid:pk>/", match_detail, name="shared-capacity-match-detail"),
    path("matches/<uuid:pk>/accept/", match_accept, name="shared-capacity-match-accept"),
    path("matches/<uuid:pk>/decline/", match_decline, name="shared-capacity-match-decline"),
    path("matches/<uuid:pk>/fulfill/", match_fulfill, name="shared-capacity-match-fulfill"),
    path("radiologist-shifts/", shift_list, name="shared-capacity-shift-list"),
    path("radiologist-shifts/post-shift/", shift_post, name="shared-capacity-shift-post"),
    path("radiologist-shifts/<uuid:pk>/", shift_detail, name="shared-capacity-shift-detail"),
    path(
        "radiologist-shifts/<uuid:pk>/increment-load/",
        shift_increment,
        name="shared-capacity-shift-increment",
    ),
]
