from rest_framework.routers import DefaultRouter

from .views import EInvoiceDocumentViewSet, InvoiceViewSet, TaxProfileViewSet

router = DefaultRouter()
router.register(r"tax-profiles", TaxProfileViewSet, basename="tax-profile")
router.register(r"invoices", InvoiceViewSet, basename="invoice")
router.register(r"documents", EInvoiceDocumentViewSet, basename="einvoice-document")

urlpatterns = router.urls
