from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cymed.provider_portal.rounding.views import (
    ClinicalRoundViewSet,
    RoundActionViewSet,
    RoundChecklistViewSet,
    RoundFindingViewSet,
    RoundTeamViewSet,
)

router = DefaultRouter()
router.register(r"rounds", ClinicalRoundViewSet, basename="clinical-round")
router.register(r"team-members", RoundTeamViewSet, basename="round-team")
router.register(r"checklists", RoundChecklistViewSet, basename="round-checklist")
router.register(r"findings", RoundFindingViewSet, basename="round-finding")
router.register(r"actions", RoundActionViewSet, basename="round-action")

urlpatterns = [
    path("", include(router.urls)),
]
