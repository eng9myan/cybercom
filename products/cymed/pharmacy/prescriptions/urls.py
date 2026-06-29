"""Prescriptions app URL routing."""

from rest_framework.routers import DefaultRouter

from .views import (
    MedicationHistoryViewSet,
    MedicationOrderViewSet,
    MedicationRefillViewSet,
    MedicationRenewalViewSet,
    PrescriptionAttachmentViewSet,
    PrescriptionItemViewSet,
    PrescriptionViewSet,
)

router = DefaultRouter()
router.register(r"rx", PrescriptionViewSet, basename="prescription")
router.register(r"items", PrescriptionItemViewSet, basename="prescription-item")
router.register(r"orders", MedicationOrderViewSet, basename="medication-order")
router.register(r"renewals", MedicationRenewalViewSet, basename="medication-renewal")
router.register(r"refills", MedicationRefillViewSet, basename="medication-refill")
router.register(r"attachments", PrescriptionAttachmentViewSet, basename="prescription-attachment")
router.register(r"history", MedicationHistoryViewSet, basename="medication-history")

urlpatterns = router.urls
