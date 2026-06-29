from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cymed.provider_portal.orders.views import (
    OrderModificationViewSet,
    OrderSetViewSet,
    OrderStatusUpdateViewSet,
    ProviderOrderRequestViewSet,
)

router = DefaultRouter()
router.register(r"order-requests", ProviderOrderRequestViewSet, basename="provider-order-request")
router.register(r"modifications", OrderModificationViewSet, basename="order-modification")
router.register(r"status-updates", OrderStatusUpdateViewSet, basename="order-status-update")
router.register(r"order-sets", OrderSetViewSet, basename="order-set")

urlpatterns = [
    path("", include(router.urls)),
]
