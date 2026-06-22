from django.urls import path, include
from rest_framework.routers import DefaultRouter
from products.cymed.clinic.triage.views import (
    TriageAssessmentViewSet, TriageVitalSignsViewSet, TriageRiskScoreViewSet
)

router = DefaultRouter()
router.register("assessments", TriageAssessmentViewSet)
router.register("vitals", TriageVitalSignsViewSet)
router.register("risk-scores", TriageRiskScoreViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
