from django.urls import path, include
from rest_framework.routers import DefaultRouter
from products.cymed.hospital.maternity.views import (
    PregnancyViewSet, PrenatalEncounterViewSet, LaborEpisodeViewSet,
    DeliveryViewSet, NewbornRecordViewSet, PostpartumCareViewSet
)

router = DefaultRouter()
router.register("pregnancies", PregnancyViewSet)
router.register("prenatal-encounters", PrenatalEncounterViewSet)
router.register("labor-episodes", LaborEpisodeViewSet)
router.register("deliveries", DeliveryViewSet)
router.register("newborns", NewbornRecordViewSet)
router.register("postpartum-checks", PostpartumCareViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
