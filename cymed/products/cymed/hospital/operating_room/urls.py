from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cymed.hospital.operating_room.views import (
    ProcedureBookingViewSet,
    ProcedureChecklistViewSet,
    ProcedureConsentViewSet,
    SurgicalCaseViewSet,
    SurgicalEquipmentViewSet,
    SurgicalScheduleViewSet,
    SurgicalTeamViewSet,
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
