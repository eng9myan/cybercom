from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.pos.views import POSOrderViewSet, POSSessionViewSet

router = DefaultRouter()
router.register("sessions", POSSessionViewSet)
router.register("orders", POSOrderViewSet)

urlpatterns = [path("", include(router.urls))]
