from django.urls import path, include
from rest_framework.routers import DefaultRouter
from products.cymed.core.encounters.views import EncounterViewSet, EpisodeOfCareViewSet

router = DefaultRouter()
router.register(r"episodes", EpisodeOfCareViewSet, basename="episode-of-care")
router.register(r"", EncounterViewSet, basename="encounter")

urlpatterns = [
    path("", include(router.urls)),
]
