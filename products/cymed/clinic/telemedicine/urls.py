from django.urls import path, include
from rest_framework.routers import DefaultRouter
from products.cymed.clinic.telemedicine.views import (
    VirtualVisitViewSet, VirtualSessionViewSet, VirtualRecordingViewSet, VirtualConsentViewSet
)

router = DefaultRouter()
router.register("visits", VirtualVisitViewSet)
router.register("sessions", VirtualSessionViewSet)
router.register("recordings", VirtualRecordingViewSet)
router.register("consents", VirtualConsentViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
