from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.procurement.views import (
    PurchaseOrderViewSet,
    PurchaseRequestViewSet,
    RequestForQuotationViewSet,
    VendorBidViewSet,
)

router = DefaultRouter()
router.register("requests", PurchaseRequestViewSet)
router.register("orders", PurchaseOrderViewSet)
router.register("rfqs", RequestForQuotationViewSet)
router.register("bids", VendorBidViewSet)

urlpatterns = [path("", include(router.urls))]
