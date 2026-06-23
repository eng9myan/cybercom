"""Inventory Bridge URL routing."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MedicationConsumptionEventViewSet, InventoryQueryView

router = DefaultRouter()
router.register(r"consumption", MedicationConsumptionEventViewSet, basename="med-consumption")

urlpatterns = [
    path("", include(router.urls)),
    path("query/", InventoryQueryView.as_view(), name="inventory-query"),
]
