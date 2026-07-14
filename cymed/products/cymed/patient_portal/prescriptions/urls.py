from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(
    r"prescriptions",
    views.PortalPrescriptionViewViewSet,
    basename="portal-prescription",
)
router.register(
    r"refill-requests",
    views.RefillRequestViewSet,
    basename="refill-request",
)
router.register(
    r"medication-instructions",
    views.MedicationInstructionViewSet,
    basename="medication-instruction",
)
router.register(
    r"adherence-logs",
    views.MedicationAdherenceLogViewSet,
    basename="medication-adherence-log",
)

urlpatterns = [path("", include(router.urls))]
