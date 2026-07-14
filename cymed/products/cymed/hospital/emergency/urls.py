from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cymed.hospital.emergency.views import (
    EmergencyAcuityViewSet,
    EmergencyDispositionViewSet,
    EmergencyObservationViewSet,
    EmergencyTrackingViewSet,
    EmergencyTriageViewSet,
    EmergencyVisitViewSet,
)

router = DefaultRouter()
router.register("visits", EmergencyVisitViewSet)
router.register("triage", EmergencyTriageViewSet)
router.register("acuities", EmergencyAcuityViewSet)
router.register("dispositions", EmergencyDispositionViewSet)
router.register("observations", EmergencyObservationViewSet)
router.register("tracking", EmergencyTrackingViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
