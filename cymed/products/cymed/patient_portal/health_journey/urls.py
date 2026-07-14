from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"timelines", views.HealthTimelineViewSet, basename="health-timeline")
router.register(
    r"timeline-events",
    views.HealthTimelineEventViewSet,
    basename="health-timeline-event",
)
router.register(r"journeys", views.PatientJourneyViewSet, basename="patient-journey")
router.register(
    r"milestones",
    views.HealthMilestoneViewSet,
    basename="health-milestone",
)
router.register(
    r"care-episodes",
    views.CareEpisodeViewSet,
    basename="care-episode",
)

urlpatterns = [path("", include(router.urls))]
