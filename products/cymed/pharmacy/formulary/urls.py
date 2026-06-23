"""Formulary URL routing."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TherapeuticClassViewSet, FormularyViewSet, FormularyDrugViewSet,
    FormularyRestrictionViewSet, PreferredMedicationViewSet
)

router = DefaultRouter()
router.register(r"therapeutic-classes", TherapeuticClassViewSet, basename="therapeutic-class")
router.register(r"formularies", FormularyViewSet, basename="formulary")
router.register(r"drugs", FormularyDrugViewSet, basename="formulary-drug")
router.register(r"restrictions", FormularyRestrictionViewSet, basename="formulary-restriction")
router.register(r"preferred", PreferredMedicationViewSet, basename="preferred-medication")

urlpatterns = router.urls
