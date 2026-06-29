from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cymed.clinic.referrals.views import (
    ReferralAttachmentViewSet,
    ReferralProviderViewSet,
    ReferralReasonViewSet,
    ReferralViewSet,
)

router = DefaultRouter()
router.register("records", ReferralViewSet)
router.register("reasons", ReferralReasonViewSet)
router.register("providers", ReferralProviderViewSet)
router.register("attachments", ReferralAttachmentViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
