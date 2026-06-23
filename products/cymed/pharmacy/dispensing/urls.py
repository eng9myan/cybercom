"""Dispensing app URL routing."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DispenseOrderViewSet, DispenseItemViewSet, DispenseBatchViewSet,
    DispenseVerificationViewSet, DispenseAuditViewSet
)

router = DefaultRouter()
router.register(r"orders", DispenseOrderViewSet, basename="dispense-order")
router.register(r"items", DispenseItemViewSet, basename="dispense-item")
router.register(r"batches", DispenseBatchViewSet, basename="dispense-batch")
router.register(r"verifications", DispenseVerificationViewSet, basename="dispense-verification")
router.register(r"audit", DispenseAuditViewSet, basename="dispense-audit")

urlpatterns = router.urls
