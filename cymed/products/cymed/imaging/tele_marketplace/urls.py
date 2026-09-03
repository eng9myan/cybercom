"""URL routes for teleradiology marketplace endpoints."""

from __future__ import annotations

from django.urls import path

from .views import (
    BidViewSet,
    RadiologistProviderViewSet,
    ReadContractViewSet,
    TeleReadJobViewSet,
    TeleReportViewSet,
)

urlpatterns = [
    path(
        "providers/",
        RadiologistProviderViewSet.as_view({"get": "list", "post": "create"}),
        name="tele-marketplace-provider-list",
    ),
    path(
        "providers/<uuid:pk>/",
        RadiologistProviderViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="tele-marketplace-provider-detail",
    ),
    path(
        "providers/onboard/",
        RadiologistProviderViewSet.as_view({"post": "onboard"}),
        name="tele-marketplace-provider-onboard",
    ),
    path(
        "contracts/",
        ReadContractViewSet.as_view({"get": "list", "post": "create"}),
        name="tele-marketplace-contract-list",
    ),
    path(
        "contracts/<uuid:pk>/",
        ReadContractViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="tele-marketplace-contract-detail",
    ),
    path(
        "contracts/sign/",
        ReadContractViewSet.as_view({"post": "sign"}),
        name="tele-marketplace-contract-sign",
    ),
    path(
        "jobs/",
        TeleReadJobViewSet.as_view({"get": "list", "post": "create"}),
        name="tele-marketplace-job-list",
    ),
    path(
        "jobs/<uuid:pk>/",
        TeleReadJobViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="tele-marketplace-job-detail",
    ),
    path(
        "jobs/post-job/",
        TeleReadJobViewSet.as_view({"post": "post_job"}),
        name="tele-marketplace-job-post",
    ),
    path(
        "jobs/<uuid:pk>/finalize/",
        TeleReadJobViewSet.as_view({"post": "finalize"}),
        name="tele-marketplace-job-finalize",
    ),
    path(
        "jobs/<uuid:pk>/dispute/",
        TeleReadJobViewSet.as_view({"post": "dispute"}),
        name="tele-marketplace-job-dispute",
    ),
    path(
        "bids/",
        BidViewSet.as_view({"get": "list", "post": "create"}),
        name="tele-marketplace-bid-list",
    ),
    path(
        "bids/<uuid:pk>/",
        BidViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="tele-marketplace-bid-detail",
    ),
    path(
        "bids/submit/",
        BidViewSet.as_view({"post": "submit"}),
        name="tele-marketplace-bid-submit",
    ),
    path(
        "bids/<uuid:pk>/accept/",
        BidViewSet.as_view({"post": "accept"}),
        name="tele-marketplace-bid-accept",
    ),
    path(
        "reports/",
        TeleReportViewSet.as_view({"get": "list", "post": "create"}),
        name="tele-marketplace-report-list",
    ),
    path(
        "reports/<uuid:pk>/",
        TeleReportViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="tele-marketplace-report-detail",
    ),
    path(
        "reports/submit/",
        TeleReportViewSet.as_view({"post": "submit"}),
        name="tele-marketplace-report-submit",
    ),
]
