from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cyed.procurement.views import (
    GoodsReceiptViewSet,
    PurchaseOrderLineViewSet,
    PurchaseOrderViewSet,
    PurchaseRequestLineViewSet,
    PurchaseRequestViewSet,
    SupplierViewSet,
)

router = DefaultRouter()
router.register("suppliers", SupplierViewSet)
router.register("requests", PurchaseRequestViewSet)
router.register("request-lines", PurchaseRequestLineViewSet)
router.register("purchase-orders", PurchaseOrderViewSet)
router.register("order-lines", PurchaseOrderLineViewSet)
router.register("goods-receipts", GoodsReceiptViewSet)

urlpatterns = [path("", include(router.urls))]
