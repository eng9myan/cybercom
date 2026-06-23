from django.urls import path, include
from rest_framework.routers import DefaultRouter
from products.cymed.hospital.transfer_center.views import (
    ReceivingFacilityViewSet, TransferCaseViewSet, ExternalReferralViewSet,
    AcceptanceReviewViewSet
)

router = DefaultRouter()
router.register("facilities", ReceivingFacilityViewSet)
router.register("cases", TransferCaseViewSet)
router.register("referrals", ExternalReferralViewSet)
router.register("reviews", AcceptanceReviewViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
