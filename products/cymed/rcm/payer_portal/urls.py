from rest_framework.routers import DefaultRouter
from .views import (
    PayerPortalAccountViewSet, PayerDashboardViewSet,
    PayerClaimReviewViewSet, PayerAuthorizationReviewViewSet,
)

router = DefaultRouter()
router.register(r"accounts", PayerPortalAccountViewSet, basename="payer-account")
router.register(r"dashboard", PayerDashboardViewSet, basename="payer-dashboard")
router.register(r"claim-reviews", PayerClaimReviewViewSet, basename="payer-claim-review")
router.register(r"auth-reviews", PayerAuthorizationReviewViewSet, basename="payer-auth-review")

urlpatterns = router.urls
