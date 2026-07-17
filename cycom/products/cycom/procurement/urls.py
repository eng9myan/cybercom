from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.procurement.views import PurchaseOrderViewSet, PurchaseRequestViewSet

router = DefaultRouter()
router.register("requests", PurchaseRequestViewSet)
router.register("orders", PurchaseOrderViewSet)

urlpatterns = [path("", include(router.urls))]
