from django.urls import path, include
from rest_framework.routers import DefaultRouter
from products.cymed.clinic.referrals.views import (
    ReferralViewSet, ReferralReasonViewSet, ReferralProviderViewSet, ReferralAttachmentViewSet
)

router = DefaultRouter()
router.register("records", ReferralViewSet)
router.register("reasons", ReferralReasonViewSet)
router.register("providers", ReferralProviderViewSet)
router.register("attachments", ReferralAttachmentViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
