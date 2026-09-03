"""URL patterns for CyMed ecosystem-wide loyalty API."""
from __future__ import annotations

from django.urls import path

from .views import (
    EcosystemAccountViewSet,
    EcosystemPointsEventViewSet,
    EcosystemProgramViewSet,
    EcosystemRedemptionViewSet,
    EcosystemRewardViewSet,
    EcosystemTierViewSet,
)

program_list = EcosystemProgramViewSet.as_view({"get": "list", "post": "create"})
program_detail = EcosystemProgramViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)
program_enroll = EcosystemProgramViewSet.as_view({"post": "enroll"})

account_list = EcosystemAccountViewSet.as_view({"get": "list", "post": "create"})
account_detail = EcosystemAccountViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)
account_earn = EcosystemAccountViewSet.as_view({"post": "earn"})
account_redeem = EcosystemAccountViewSet.as_view({"post": "redeem"})
account_transfer_out = EcosystemAccountViewSet.as_view({"post": "transfer_out"})
account_expire = EcosystemAccountViewSet.as_view({"post": "expire"})
account_manual_adjust = EcosystemAccountViewSet.as_view({"post": "manual_adjust"})

tier_list = EcosystemTierViewSet.as_view({"get": "list", "post": "create"})
tier_detail = EcosystemTierViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)

event_list = EcosystemPointsEventViewSet.as_view({"get": "list"})
event_detail = EcosystemPointsEventViewSet.as_view({"get": "retrieve"})

reward_list = EcosystemRewardViewSet.as_view({"get": "list", "post": "create"})
reward_detail = EcosystemRewardViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)

redemption_list = EcosystemRedemptionViewSet.as_view({"get": "list", "post": "create"})
redemption_detail = EcosystemRedemptionViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)

urlpatterns = [
    path("programs/", program_list, name="rewards-program-list"),
    path("programs/enroll/", program_enroll, name="rewards-program-enroll"),
    path("programs/<uuid:pk>/", program_detail, name="rewards-program-detail"),
    path("accounts/", account_list, name="rewards-account-list"),
    path("accounts/<uuid:pk>/", account_detail, name="rewards-account-detail"),
    path("accounts/<uuid:pk>/earn/", account_earn, name="rewards-account-earn"),
    path("accounts/<uuid:pk>/redeem/", account_redeem, name="rewards-account-redeem"),
    path("accounts/<uuid:pk>/transfer-out/", account_transfer_out, name="rewards-account-transfer-out"),
    path("accounts/<uuid:pk>/expire/", account_expire, name="rewards-account-expire"),
    path("accounts/<uuid:pk>/manual-adjust/", account_manual_adjust, name="rewards-account-manual-adjust"),
    path("tiers/", tier_list, name="rewards-tier-list"),
    path("tiers/<uuid:pk>/", tier_detail, name="rewards-tier-detail"),
    path("events/", event_list, name="rewards-event-list"),
    path("events/<uuid:pk>/", event_detail, name="rewards-event-detail"),
    path("rewards/", reward_list, name="rewards-reward-list"),
    path("rewards/<uuid:pk>/", reward_detail, name="rewards-reward-detail"),
    path("redemptions/", redemption_list, name="rewards-redemption-list"),
    path("redemptions/<uuid:pk>/", redemption_detail, name="rewards-redemption-detail"),
]
