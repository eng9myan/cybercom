"""Analytics URL routing."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PharmacyDashboardSnapshotViewSet, MedicationSafetyEventViewSet,
    PharmacyAnalyticsConfigViewSet, PharmacyOperationsDashboardView, MedicationSafetyDashboardView
)

router = DefaultRouter()
router.register(r"snapshots", PharmacyDashboardSnapshotViewSet, basename="pharmacy-snapshot")
router.register(r"safety-events", MedicationSafetyEventViewSet, basename="safety-event")
router.register(r"config", PharmacyAnalyticsConfigViewSet, basename="analytics-config")

urlpatterns = [
    path("", include(router.urls)),
    path("dashboard/operations/", PharmacyOperationsDashboardView.as_view(), name="pharmacy-operations-dashboard"),
    path("dashboard/safety/", MedicationSafetyDashboardView.as_view(), name="medication-safety-dashboard"),
]
