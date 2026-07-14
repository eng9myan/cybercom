from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cymed.clinic.triage.views import (
    TriageAssessmentViewSet,
    TriageRiskScoreViewSet,
    TriageVitalSignsViewSet,
)

router = DefaultRouter()
router.register("assessments", TriageAssessmentViewSet)
router.register("vitals", TriageVitalSignsViewSet)
router.register("risk-scores", TriageRiskScoreViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
