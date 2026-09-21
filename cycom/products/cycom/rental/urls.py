from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.rental.views import RentalOrderLineViewSet, RentalOrderViewSet

router = DefaultRouter()
router.register("orders", RentalOrderViewSet)
router.register("lines", RentalOrderLineViewSet)

urlpatterns = [path("", include(router.urls))]
