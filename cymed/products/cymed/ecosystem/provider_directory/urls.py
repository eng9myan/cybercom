"""URL routes for provider directory API."""
from __future__ import annotations

from django.urls import path

from .views import (
    DirectoryReviewViewSet,
    NetworkFacilityViewSet,
    NetworkPractitionerViewSet,
    PractitionerFacilityAffiliationViewSet,
)


urlpatterns = [
    path(
        "facilities/",
        NetworkFacilityViewSet.as_view({"get": "list", "post": "create"}),
        name="cymed-eco-provider-directory-facility-list",
    ),
    path(
        "facilities/<uuid:pk>/",
        NetworkFacilityViewSet.as_view(
            {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
        ),
        name="cymed-eco-provider-directory-facility-detail",
    ),
    path(
        "facilities/register/",
        NetworkFacilityViewSet.as_view({"post": "register"}),
        name="cymed-eco-provider-directory-facility-register",
    ),
    path(
        "facilities/search/",
        NetworkFacilityViewSet.as_view({"post": "search"}),
        name="cymed-eco-provider-directory-facility-search",
    ),
    path(
        "practitioners/",
        NetworkPractitionerViewSet.as_view({"get": "list", "post": "create"}),
        name="cymed-eco-provider-directory-practitioner-list",
    ),
    path(
        "practitioners/<uuid:pk>/",
        NetworkPractitionerViewSet.as_view(
            {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
        ),
        name="cymed-eco-provider-directory-practitioner-detail",
    ),
    path(
        "practitioners/register/",
        NetworkPractitionerViewSet.as_view({"post": "register"}),
        name="cymed-eco-provider-directory-practitioner-register",
    ),
    path(
        "practitioners/search/",
        NetworkPractitionerViewSet.as_view({"post": "search"}),
        name="cymed-eco-provider-directory-practitioner-search",
    ),
    path(
        "practitioners/affiliate/",
        NetworkPractitionerViewSet.as_view({"post": "affiliate"}),
        name="cymed-eco-provider-directory-practitioner-affiliate",
    ),
    path(
        "affiliations/",
        PractitionerFacilityAffiliationViewSet.as_view({"get": "list", "post": "create"}),
        name="cymed-eco-provider-directory-affiliation-list",
    ),
    path(
        "affiliations/<uuid:pk>/",
        PractitionerFacilityAffiliationViewSet.as_view(
            {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
        ),
        name="cymed-eco-provider-directory-affiliation-detail",
    ),
    path(
        "reviews/",
        DirectoryReviewViewSet.as_view({"get": "list", "post": "create"}),
        name="cymed-eco-provider-directory-review-list",
    ),
    path(
        "reviews/<uuid:pk>/",
        DirectoryReviewViewSet.as_view(
            {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
        ),
        name="cymed-eco-provider-directory-review-detail",
    ),
    path(
        "reviews/post/",
        DirectoryReviewViewSet.as_view({"post": "post_review"}),
        name="cymed-eco-provider-directory-review-post",
    ),
    path(
        "reviews/<uuid:pk>/moderate/",
        DirectoryReviewViewSet.as_view({"post": "moderate"}),
        name="cymed-eco-provider-directory-review-moderate",
    ),
]
