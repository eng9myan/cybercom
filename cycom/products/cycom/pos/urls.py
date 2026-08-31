from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.pos.views import (
    DeviceViewSet,
    POSOrderViewSet,
    POSSessionViewSet,
    PosReceiptViewSet,
)

router = DefaultRouter()
router.register("sessions", POSSessionViewSet)
router.register("orders", POSOrderViewSet)
router.register("devices", DeviceViewSet)
router.register("receipts", PosReceiptViewSet)

urlpatterns = [path("", include(router.urls))]
