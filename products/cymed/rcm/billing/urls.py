from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PatientAccountViewSet,
    EncounterBillingViewSet,
    InvoiceViewSet,
    InvoiceLineViewSet,
    BillingAdjustmentViewSet,
    RefundViewSet,
)

router = DefaultRouter()
router.register(r"patient-accounts", PatientAccountViewSet, basename="patient-account")
router.register(r"encounter-billings", EncounterBillingViewSet, basename="encounter-billing")
router.register(r"invoices", InvoiceViewSet, basename="invoice")
router.register(r"invoice-lines", InvoiceLineViewSet, basename="invoice-line")
router.register(r"adjustments", BillingAdjustmentViewSet, basename="billing-adjustment")
router.register(r"refunds", RefundViewSet, basename="refund")

urlpatterns = [
    path("", include(router.urls)),
]
