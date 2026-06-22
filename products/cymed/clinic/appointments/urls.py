from django.urls import path, include
from rest_framework.routers import DefaultRouter
from products.cymed.clinic.appointments.views import (
    ClinicAppointmentViewSet, AppointmentReminderViewSet,
    AppointmentWaitlistViewSet, AppointmentTemplateViewSet, AppointmentRuleViewSet
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
