from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(
    r'requests',
    views.PortalAppointmentRequestViewSet,
    basename='portal-appointment-request',
)
router.register(
    r'waitlist',
    views.WaitlistEntryViewSet,
    basename='portal-waitlist-entry',
)
router.register(
    r'reminders',
    views.AppointmentReminderViewSet,
    basename='portal-appointment-reminder',
)
router.register(
    r'ratings',
    views.AppointmentRatingViewSet,
    basename='portal-appointment-rating',
)

urlpatterns = [path('', include(router.urls))]
