"""URL routes for the cross-provider referral routing sub-app."""
from __future__ import annotations

from django.urls import path

from .views import NetworkReferralViewSet, RoutingLogViewSet, RoutingRuleViewSet


urlpatterns = [
    path(
        "routing-rules/",
        RoutingRuleViewSet.as_view({"get": "list", "post": "create"}),
        name="referral-routing-rule-list",
    ),
    path(
        "routing-rules/<uuid:pk>/",
        RoutingRuleViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="referral-routing-rule-detail",
    ),
    path(
        "routing-rules/create-rule/",
        RoutingRuleViewSet.as_view({"post": "create_rule"}),
        name="referral-routing-rule-create-rule",
    ),
    path(
        "referrals/",
        NetworkReferralViewSet.as_view({"get": "list", "post": "create"}),
        name="referral-routing-referral-list",
    ),
    path(
        "referrals/<uuid:pk>/",
        NetworkReferralViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="referral-routing-referral-detail",
    ),
    path(
        "referrals/route/",
        NetworkReferralViewSet.as_view({"post": "route"}),
        name="referral-routing-referral-route",
    ),
    path(
        "referrals/<uuid:pk>/acknowledge/",
        NetworkReferralViewSet.as_view({"post": "acknowledge"}),
        name="referral-routing-referral-acknowledge",
    ),
    path(
        "referrals/<uuid:pk>/decline/",
        NetworkReferralViewSet.as_view({"post": "decline"}),
        name="referral-routing-referral-decline",
    ),
    path(
        "referrals/<uuid:pk>/manual-override/",
        NetworkReferralViewSet.as_view({"post": "manual_override"}),
        name="referral-routing-referral-manual-override",
    ),
    path(
        "referrals/<uuid:pk>/mark-scheduled/",
        NetworkReferralViewSet.as_view({"post": "mark_scheduled"}),
        name="referral-routing-referral-mark-scheduled",
    ),
    path(
        "referrals/<uuid:pk>/mark-completed/",
        NetworkReferralViewSet.as_view({"post": "mark_completed"}),
        name="referral-routing-referral-mark-completed",
    ),
    path(
        "referrals/<uuid:pk>/attach-result/",
        NetworkReferralViewSet.as_view({"post": "attach_result"}),
        name="referral-routing-referral-attach-result",
    ),
    path(
        "logs/",
        RoutingLogViewSet.as_view({"get": "list"}),
        name="referral-routing-log-list",
    ),
    path(
        "logs/<uuid:pk>/",
        RoutingLogViewSet.as_view({"get": "retrieve"}),
        name="referral-routing-log-detail",
    ),
]
