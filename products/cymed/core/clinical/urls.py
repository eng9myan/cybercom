from django.urls import path, include
from rest_framework.routers import DefaultRouter
from products.cymed.core.clinical.views import (
    ConditionViewSet, AllergyViewSet, VitalSignViewSet, ObservationViewSet, ClinicalFlagViewSet, BreakGlassView
)

router = DefaultRouter()
router.register(r"conditions", ConditionViewSet, basename="condition")
router.register(r"allergies", AllergyViewSet, basename="allergy")
router.register(r"vitals", VitalSignViewSet, basename="vitals")
router.register(r"observations", ObservationViewSet, basename="observation")
router.register(r"flags", ClinicalFlagViewSet, basename="flag")

urlpatterns = [
    path("breakglass/", BreakGlassView.as_view(), name="breakglass"),
    path("", include(router.urls)),
]
