from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.ar_ap.views import InvoiceViewSet, PartnerViewSet, PaymentViewSet

router = DefaultRouter()
router.register("partners", PartnerViewSet)
router.register("invoices", InvoiceViewSet)
router.register("payments", PaymentViewSet)

urlpatterns = [path("", include(router.urls))]
