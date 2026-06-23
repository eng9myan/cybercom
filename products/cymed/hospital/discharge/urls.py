from django.urls import path, include
from rest_framework.routers import DefaultRouter
from products.cymed.hospital.discharge.views import (
    DischargeChecklistViewSet, DischargeMedicationViewSet, FollowUpAppointmentViewSet,
    DischargeInstructionViewSet
)

router = DefaultRouter()
router.register("checklists", DischargeChecklistViewSet)
router.register("medications", DischargeMedicationViewSet)
router.register("followups", FollowUpAppointmentViewSet)
router.register("instructions", DischargeInstructionViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
