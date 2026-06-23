from django.urls import path, include
from rest_framework.routers import DefaultRouter
from products.cymed.hospital.operating_room.views import (
    SurgicalCaseViewSet, SurgicalScheduleViewSet, ProcedureBookingViewSet,
    ProcedureConsentViewSet, ProcedureChecklistViewSet, SurgicalTeamViewSet,
    SurgicalEquipmentViewSet
)

router = DefaultRouter()
router.register("cases", SurgicalCaseViewSet)
router.register("schedules", SurgicalScheduleViewSet)
router.register("bookings", ProcedureBookingViewSet)
router.register("consents", ProcedureConsentViewSet)
router.register("checklists", ProcedureChecklistViewSet)
router.register("teams", SurgicalTeamViewSet)
router.register("equipment", SurgicalEquipmentViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
