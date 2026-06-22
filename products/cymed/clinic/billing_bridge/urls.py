from django.urls import path, include
from rest_framework.routers import DefaultRouter
from products.cymed.clinic.billing_bridge.views import (
    ChargeCodeViewSet, PriceListViewSet, ClinicServiceViewSet, ChargeItemViewSet
)

router = DefaultRouter()
router.register("codes", ChargeCodeViewSet)
router.register("pricelists", PriceListViewSet)
router.register("services", ClinicServiceViewSet)
router.register("items", ChargeItemViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
