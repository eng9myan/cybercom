from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cyed.meetings.interview_views import (
    InterviewBookingViewSet,
    InterviewRoundViewSet,
    InterviewSlotViewSet,
)
from products.cyed.meetings.views import MeetingSessionViewSet

router = DefaultRouter()
router.register("sessions", MeetingSessionViewSet)
router.register("interview-rounds", InterviewRoundViewSet)
router.register("interview-slots", InterviewSlotViewSet)
router.register("interview-bookings", InterviewBookingViewSet)

urlpatterns = [path("", include(router.urls))]
