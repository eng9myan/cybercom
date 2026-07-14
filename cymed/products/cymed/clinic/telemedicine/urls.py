from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cymed.clinic.telemedicine.views import (
    VirtualConsentViewSet,
    VirtualRecordingViewSet,
    VirtualSessionViewSet,
    VirtualVisitViewSet,
)

router = DefaultRouter()
router.register("visits", VirtualVisitViewSet)
router.register("sessions", VirtualSessionViewSet)
router.register("recordings", VirtualRecordingViewSet)
router.register("consents", VirtualConsentViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
