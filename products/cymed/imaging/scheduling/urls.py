from rest_framework.routers import DefaultRouter
from .views import ImagingRoomViewSet, ImagingAppointmentViewSet, ModalityScheduleViewSet, RadiologistScheduleViewSet

router = DefaultRouter()
router.register("rooms", ImagingRoomViewSet, basename="imaging-room")
router.register("appointments", ImagingAppointmentViewSet, basename="imaging-appointment")
router.register("modality-schedules", ModalityScheduleViewSet, basename="modality-schedule")
router.register("radiologist-schedules", RadiologistScheduleViewSet, basename="radiologist-schedule")

urlpatterns = router.urls
