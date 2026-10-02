from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cymed.core.orders.views import OrderSetViewSet

# Separate prefix: the orders router is registered at r"" so "sets/" there
# would be swallowed by the order detail route.
router = DefaultRouter()
router.register(r"", OrderSetViewSet, basename="order-set")

urlpatterns = [
    path("", include(router.urls)),
]
