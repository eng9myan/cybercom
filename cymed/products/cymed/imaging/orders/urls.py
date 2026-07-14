from rest_framework.routers import DefaultRouter

from .views import (
    ImagingOrderItemViewSet,
    ImagingOrderStatusHistoryViewSet,
    ImagingOrderViewSet,
    ImagingProcedureViewSet,
    ImagingProtocolViewSet,
)

router = DefaultRouter()
router.register("protocols", ImagingProtocolViewSet, basename="imaging-protocol")
router.register("procedures", ImagingProcedureViewSet, basename="imaging-procedure")
router.register("orders", ImagingOrderViewSet, basename="imaging-order")
router.register("order-items", ImagingOrderItemViewSet, basename="imaging-order-item")
router.register("order-history", ImagingOrderStatusHistoryViewSet, basename="imaging-order-history")

urlpatterns = router.urls
