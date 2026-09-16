from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cyed.events.views import EventParticipationViewSet, EventViewSet

router = DefaultRouter()
router.register("events", EventViewSet)
router.register("participations", EventParticipationViewSet)

urlpatterns = [path("", include(router.urls))]
