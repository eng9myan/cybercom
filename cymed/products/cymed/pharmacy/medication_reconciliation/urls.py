"""Medication Reconciliation URL routing."""

from rest_framework.routers import DefaultRouter

from .views import (
    MedicationChangeViewSet,
    MedicationConflictViewSet,
    MedicationReconciliationViewSet,
)

router = DefaultRouter()
router.register(r"", MedicationReconciliationViewSet, basename="med-reconciliation")
router.register(r"changes", MedicationChangeViewSet, basename="medication-change")
router.register(r"conflicts", MedicationConflictViewSet, basename="medication-conflict")

urlpatterns = router.urls
