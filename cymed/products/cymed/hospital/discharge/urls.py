from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cymed.hospital.discharge.views import (
    DischargeChecklistViewSet,
    DischargeInstructionViewSet,
    DischargeMedicationViewSet,
    FollowUpAppointmentViewSet,
)

router = DefaultRouter()
router.register("checklists", DischargeChecklistViewSet)
router.register("medications", DischargeMedicationViewSet)
router.register("followups", FollowUpAppointmentViewSet)
router.register("instructions", DischargeInstructionViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
