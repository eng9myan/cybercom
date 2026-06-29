from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cymed.clinic.appointments.views import (
    AppointmentReminderViewSet,
    AppointmentRuleViewSet,
    AppointmentTemplateViewSet,
    AppointmentWaitlistViewSet,
    ClinicAppointmentViewSet,
)

router = DefaultRouter()
router.register("bookings", ClinicAppointmentViewSet)
router.register("reminders", AppointmentReminderViewSet)
router.register("waitlist", AppointmentWaitlistViewSet)
router.register("templates", AppointmentTemplateViewSet)
router.register("rules", AppointmentRuleViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
