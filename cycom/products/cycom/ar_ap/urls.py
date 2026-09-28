from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.ar_ap.einvoice_views import (
    EInvoiceProfileView,
    InvoiceEInvoiceDocumentView,
    InvoiceEInvoiceRetryView,
    InvoiceEInvoiceView,
)
from products.cycom.ar_ap.views import InvoiceViewSet, PartnerViewSet, PaymentViewSet

router = DefaultRouter()
router.register("partners", PartnerViewSet)
router.register("invoices", InvoiceViewSet)
router.register("payments", PaymentViewSet)

urlpatterns = [
    path("einvoice-profile/", EInvoiceProfileView.as_view()),
    path("invoices/<uuid:pk>/einvoice/", InvoiceEInvoiceView.as_view()),
    path("invoices/<uuid:pk>/einvoice/retry/", InvoiceEInvoiceRetryView.as_view()),
    path("invoices/<uuid:pk>/einvoice/document/", InvoiceEInvoiceDocumentView.as_view()),
    path("", include(router.urls)),
]
