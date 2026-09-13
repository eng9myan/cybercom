from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.pos.views import (
    DeviceViewSet,
    POSOrderViewSet,
    POSSessionViewSet,
    PosReceiptViewSet,
    PosReturnViewSet,
)

router = DefaultRouter()
router.register("sessions", POSSessionViewSet)
router.register("orders", POSOrderViewSet)
router.register("devices", DeviceViewSet)
router.register("receipts", PosReceiptViewSet)
router.register("returns", PosReturnViewSet)

urlpatterns = [path("", include(router.urls))]
