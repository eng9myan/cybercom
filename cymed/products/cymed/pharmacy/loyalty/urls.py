"""URL routes for CyMed Pharmacy Loyalty & Rewards."""
from django.urls import path

from .views import (
    LoyaltyProgramViewSet,
    LoyaltyTierViewSet,
    PatientLoyaltyAccountViewSet,
    PointsTransactionViewSet,
    RedemptionViewSet,
    RewardViewSet,
)

urlpatterns = [
    path(
        "programs/",
        LoyaltyProgramViewSet.as_view({"get": "list", "post": "create"}),
        name="loyalty-program-list",
    ),
    path(
        "programs/<uuid:pk>/",
        LoyaltyProgramViewSet.as_view(
            {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
        ),
        name="loyalty-program-detail",
    ),
    path(
        "tiers/",
        LoyaltyTierViewSet.as_view({"get": "list", "post": "create"}),
        name="loyalty-tier-list",
    ),
    path(
        "tiers/<uuid:pk>/",
        LoyaltyTierViewSet.as_view(
            {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
        ),
        name="loyalty-tier-detail",
    ),
    path(
        "accounts/",
        PatientLoyaltyAccountViewSet.as_view({"get": "list", "post": "create"}),
        name="patient-loyalty-account-list",
    ),
    path(
        "accounts/<uuid:pk>/",
        PatientLoyaltyAccountViewSet.as_view(
            {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
        ),
        name="patient-loyalty-account-detail",
    ),
    path(
        "accounts/enroll/",
        PatientLoyaltyAccountViewSet.as_view({"post": "enroll"}),
        name="patient-loyalty-account-enroll",
    ),
    path(
        "accounts/<uuid:pk>/earn-points/",
        PatientLoyaltyAccountViewSet.as_view({"post": "earn_points"}),
        name="patient-loyalty-account-earn-points",
    ),
    path(
        "accounts/<uuid:pk>/redeem-reward/",
        PatientLoyaltyAccountViewSet.as_view({"post": "redeem_reward"}),
        name="patient-loyalty-account-redeem-reward",
    ),
    path(
        "accounts/<uuid:pk>/manual-adjust/",
        PatientLoyaltyAccountViewSet.as_view({"post": "manual_adjust"}),
        name="patient-loyalty-account-manual-adjust",
    ),
    path(
        "accounts/<uuid:pk>/expire-points/",
        PatientLoyaltyAccountViewSet.as_view({"post": "expire_points"}),
        name="patient-loyalty-account-expire-points",
    ),
    path(
        "transactions/",
        PointsTransactionViewSet.as_view({"get": "list", "post": "create"}),
        name="points-transaction-list",
    ),
    path(
        "transactions/<uuid:pk>/",
        PointsTransactionViewSet.as_view(
            {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
        ),
        name="points-transaction-detail",
    ),
    path(
        "rewards/",
        RewardViewSet.as_view({"get": "list", "post": "create"}),
        name="reward-list",
    ),
    path(
        "rewards/<uuid:pk>/",
        RewardViewSet.as_view(
            {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
        ),
        name="reward-detail",
    ),
    path(
        "redemptions/",
        RedemptionViewSet.as_view({"get": "list", "post": "create"}),
        name="redemption-list",
    ),
    path(
        "redemptions/<uuid:pk>/",
        RedemptionViewSet.as_view(
            {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
        ),
        name="redemption-detail",
    ),
]
